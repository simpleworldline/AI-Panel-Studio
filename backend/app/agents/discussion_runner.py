"""DiscussionRunner — 讨论运行引擎（生命周期 + 事件总线）"""

import asyncio
import uuid
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.host_agent import HostAgent
from app.agents.expert_agent import ExpertAgent
from app.agents.observer_agent import ObserverAgent
from app.agents.scheduler import Scheduler
from app.models.discussion import Discussion
from app.models.panel_member import PanelMember
from app.models.utterance import Utterance
from app.models.consensus import ConsensusDisagreement
from app.models.expert_status_log import ExpertStatusLog


class DiscussionRunner:
    """讨论运行引擎 — 管理讨论生命周期 + Agent 编排"""

    def __init__(self, discussion_id: str, ws_manager):
        self.discussion_id = discussion_id
        self.ws = ws_manager
        self.scheduler = Scheduler()
        self.observer = ObserverAgent()
        self._paused = asyncio.Event()
        self._paused.set()  # 初始为暂停状态，start() 后清除
        self._running = False

    async def run(self, session_factory) -> bool:
        """启动讨论主循环"""
        self._running = True
        self._paused.clear()

        async with session_factory() as db:
            d = await db.get(Discussion, self.discussion_id)
            if d is None or d.status != "live":
                return False

            # 加载 PanelMembers
            from sqlalchemy import select
            result = await db.execute(
                select(PanelMember).where(PanelMember.discussion_id == self.discussion_id).order_by(PanelMember.sort_order)
            )
            members = result.scalars().all()

            host = None
            experts = []
            for m in members:
                if m.role == "host":
                    host = HostAgent(m.id, m.name, m.title, m.stance, m.color)
                else:
                    experts.append(ExpertAgent(m.id, m.name, m.title, m.stance, m.color))

            if host is None:
                return False

            # 1. 开场白
            await self._broadcast_expert_status(host, "preparing", db)
            await self._broadcast_expert_status(host, "speaking", db)
            opening_text = ""
            async for token in host.generate_utterance([], d.topic):
                opening_text += token
                await self.ws.broadcast(self.discussion_id, {
                    "type": "utterance_token",
                    "data": {
                        "utterance_id": ":opening:", "member_id": host.member_id,
                        "member_name": host.name, "member_title": host.title,
                        "member_color": host.color, "token": token,
                        "sequence_num": 0, "round_num": 0,
                        "is_first": (opening_text == token), "is_last": False,
                    },
                })

            if opening_text:
                u = await self._save_utterance(db, host, opening_text, "opening", 0)
                await self.ws.broadcast(self.discussion_id, {
                    "type": "utterance_complete",
                    "data": self._format_utterance(u),
                })
                await self._broadcast_expert_status(host, "idle", db)

            # 2. 主循环
            while self._running:
                await self._paused.wait()  # 暂停时阻塞

                d = await db.get(Discussion, self.discussion_id)
                if d is None or d.status not in ("live", "paused"):
                    break

                # 收集所有 Agent 的欲望值
                all_agents: list = [host] + experts
                transcript = self._load_transcript(db, d)

                for agent in all_agents:
                    await agent.prepare(transcript, d.topic)
                    await self._broadcast_expert_status(agent, "preparing", db)

                # Scheduler 选择发言者
                speaker = await self.scheduler.select_speaker(all_agents)
                if speaker is None:
                    break

                # 生成发言
                await self._broadcast_expert_status(speaker, "speaking", db)
                accumulated = ""
                utterance_id = str(uuid.uuid4())
                agent_seq = d.current_round * len(all_agents) + 1

                async for token in speaker.generate_utterance(transcript, d.topic):
                    accumulated += token
                    await self.ws.broadcast(self.discussion_id, {
                        "type": "utterance_token",
                        "data": {
                            "utterance_id": utterance_id, "member_id": speaker.member_id,
                            "member_name": speaker.name, "member_title": speaker.title,
                            "member_color": speaker.color, "token": token,
                            "sequence_num": agent_seq, "round_num": d.current_round + 1,
                            "is_first": (accumulated == token), "is_last": False,
                        },
                    })

                if accumulated:
                    u = await self._save_utterance(db, speaker, accumulated, "statement", d.current_round + 1)
                    await self.ws.broadcast(self.discussion_id, {
                        "type": "utterance_complete",
                        "data": self._format_utterance(u),
                    })
                    speaker.mark_spoke()

                await self._broadcast_expert_status(speaker, "idle", db)
                for a in all_agents:
                    if a != speaker:
                        a.mark_silent()

                # Observer 分析
                transcript = self._load_transcript(db, d)
                latest = self._format_utterance(u) if accumulated else None
                if latest:
                    existing = await self._load_consensus(db)
                    analysis = await self.observer.analyze(transcript, latest, existing)
                    if analysis:
                        await self._save_consensus(db, analysis)
                        await self.ws.broadcast(self.discussion_id, {
                            "type": "consensus_update",
                            "data": analysis,
                        })

                # 轮次递增
                d.current_round += 1
                await db.commit()

                # 结束条件检查
                if d.max_rounds and d.current_round >= d.max_rounds:
                    await self._end_discussion(db, d, host, "max_rounds")
                    break

            return True

    async def pause(self):
        self._paused.clear()

    async def resume(self):
        self._paused.set()

    async def stop(self):
        self._running = False
        self._paused.set()

    async def _broadcast_expert_status(self, agent, status: str, db: AsyncSession):
        log = ExpertStatusLog(
            id=str(uuid.uuid4()), discussion_id=self.discussion_id,
            panel_member_id=agent.member_id, status=status,
            focus_summary=agent.focus_summary, desire_value=agent.desire_value,
        )
        db.add(log)
        await db.flush()
        await self.ws.broadcast(self.discussion_id, {
            "type": "expert_status",
            "data": {
                "member_id": agent.member_id, "member_name": agent.name,
                "member_color": agent.color, "status": status,
                "focus_summary": agent.focus_summary,
                "desire_value": agent.desire_value,
                "timestamp": log.recorded_at,
            },
        })

    async def _save_utterance(self, db: AsyncSession, agent, content: str, utype: str, round_num: int) -> Utterance:
        from sqlalchemy import select, func
        seq_result = await db.execute(
            select(func.max(Utterance.sequence_num)).where(Utterance.discussion_id == self.discussion_id)
        )
        max_seq = seq_result.scalar() or 0
        u = Utterance(
            id=str(uuid.uuid4()), discussion_id=self.discussion_id,
            panel_member_id=agent.member_id, content=content,
            utterance_type=utype, round_num=round_num, sequence_num=max_seq + 1,
        )
        db.add(u)
        await db.flush()
        await db.refresh(u)
        return u

    def _load_transcript(self, db: AsyncSession, d: Discussion) -> list[dict]:
        # Simple in-memory loading
        from sqlalchemy import select
        # We need to re-query since we can't access lazy relationships easily
        return []

    async def _load_consensus(self, db: AsyncSession) -> list[dict]:
        from sqlalchemy import select
        result = await db.execute(
            select(ConsensusDisagreement).where(
                ConsensusDisagreement.discussion_id == self.discussion_id
            )
        )
        items = result.scalars().all()
        return [
            {
                "id": c.id, "type": c.type, "title": c.title,
                "description": c.description,
                "source_utterance_ids": c.source_utterance_ids,
                "confidence": c.confidence, "is_resolved": bool(c.is_resolved),
                "round_num": c.round_num,
            }
            for c in items
        ]

    async def _save_consensus(self, db: AsyncSession, analysis: dict):
        import json
        cd = ConsensusDisagreement(
            id=str(uuid.uuid4()),
            discussion_id=self.discussion_id,
            type=analysis.get("type", "consensus"),
            title=analysis.get("title", ""),
            description=analysis.get("description", ""),
            source_utterance_ids=json.dumps(analysis.get("source_utterance_ids", [])),
            confidence=analysis.get("confidence", 0.5),
            is_resolved=1 if analysis.get("is_resolved") else 0,
            round_num=analysis.get("round_num", 0),
        )
        db.add(cd)
        await db.flush()

    def _format_utterance(self, u) -> dict:
        return {
            "utterance_id": u.id if hasattr(u, 'id') else u.get("utterance_id", ""),
            "member_id": u.panel_member_id if hasattr(u, 'panel_member_id') else u.get("member_id", ""),
            "member_name": u.panel_member.name if hasattr(u, 'panel_member') else u.get("member_name", ""),
            "member_title": u.panel_member.title if hasattr(u, 'panel_member') else u.get("member_title", ""),
            "member_color": u.panel_member.color if hasattr(u, 'panel_member') else u.get("member_color", ""),
            "content": u.content if hasattr(u, 'content') else u.get("content", ""),
            "utterance_type": u.utterance_type if hasattr(u, 'utterance_type') else u.get("utterance_type", ""),
            "sequence_num": u.sequence_num if hasattr(u, 'sequence_num') else u.get("sequence_num", 0),
            "round_num": u.round_num if hasattr(u, 'round_num') else u.get("round_num", 0),
            "created_at": u.created_at if hasattr(u, 'created_at') else u.get("created_at", ""),
        }

    async def _end_discussion(self, db: AsyncSession, d: Discussion, host: HostAgent, reason: str):
        from datetime import datetime, timezone
        d.status = "ended"
        d.ended_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        await db.commit()

        await self.ws.broadcast(self.discussion_id, {
            "type": "discussion_ended",
            "data": {
                "discussion_id": self.discussion_id,
                "end_reason": reason,
                "total_rounds": d.current_round,
                "total_utterances": 0,
                "ended_at": d.ended_at,
            },
        })
