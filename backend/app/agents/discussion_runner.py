"""DiscussionRunner — 讨论运行引擎（生命周期 + Agent 编排 + 事件总线）"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agents.host_agent import HostAgent
from app.agents.expert_agent import ExpertAgent
from app.agents.observer_agent import ObserverAgent
from app.agents.scheduler import Scheduler
from app.models.discussion import Discussion
from app.models.panel_member import PanelMember
from app.models.utterance import Utterance
from app.models.consensus import ConsensusDisagreement
from app.models.expert_status_log import ExpertStatusLog


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class DiscussionRunner:
    """讨论运行引擎 — 管理讨论生命周期 + Agent 编排

    每个 Running 讨论在内存中有一个 Runner 实例。
    通过 asyncio.Event 实现 pause/resume 控制。
    """

    def __init__(self, discussion_id: str, ws_manager):
        self.discussion_id = discussion_id
        self.ws = ws_manager
        self.scheduler = Scheduler()
        self.observer = ObserverAgent()
        self._paused = asyncio.Event()
        self._paused.set()      # 初始为运行状态
        self._running = False
        self._session_factory: async_sessionmaker | None = None

    async def run(self, session_factory: async_sessionmaker) -> bool:
        """启动讨论主循环 — 作为后台任务运行"""
        self._session_factory = session_factory
        self._running = True
        self._paused.set()

        async with session_factory() as db:
            d = await db.get(Discussion, self.discussion_id)
            if d is None or d.status != "live":
                return False

            # 加载 PanelMembers
            result = await db.execute(
                select(PanelMember)
                .where(PanelMember.discussion_id == self.discussion_id)
                .order_by(PanelMember.sort_order)
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

            # === 1. 开场白 ===
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

            await db.commit()

            # === 2. 主发言循环 ===
            while self._running:
                # 暂停等待
                await self._paused.wait()

                # 重新从 DB 获取讨论状态（防外部变更）
                await db.refresh(d)
                if d.status not in ("live", "paused"):
                    break

                # 检查结束条件
                if d.max_rounds and d.current_round >= d.max_rounds:
                    await self._end_discussion(db, d, host, "max_rounds")
                    break

                # 加载最新 transcript
                transcript = await self._load_transcript(db)
                all_agents: list = [host] + experts

                # 各 Agent 计算欲望值 + 发送状态
                for agent in all_agents:
                    await agent.prepare(transcript, d.topic)
                    await self._broadcast_expert_status(agent, "preparing", db)

                # Scheduler 选出发言者
                speaker = await self.scheduler.select_speaker(all_agents)
                if speaker is None:
                    await asyncio.sleep(0.5)  # 等待下一轮
                    continue

                # 生成发言（流式推送）
                await self._broadcast_expert_status(speaker, "speaking", db)
                accumulated = ""
                utterance_id = str(uuid.uuid4())
                next_seq = len(transcript) + 1

                async for token in speaker.generate_utterance(transcript, d.topic):
                    accumulated += token
                    await self.ws.broadcast(self.discussion_id, {
                        "type": "utterance_token",
                        "data": {
                            "utterance_id": utterance_id, "member_id": speaker.member_id,
                            "member_name": speaker.name, "member_title": speaker.title,
                            "member_color": speaker.color, "token": token,
                            "sequence_num": next_seq, "round_num": d.current_round + 1,
                            "is_first": (accumulated == token), "is_last": False,
                        },
                    })

                if accumulated:
                    u = await self._save_utterance(
                        db, speaker, accumulated, "statement", d.current_round + 1
                    )
                    await self.ws.broadcast(self.discussion_id, {
                        "type": "utterance_complete",
                        "data": self._format_utterance(u),
                    })
                    speaker.mark_spoke()

                # 其他 agent 标记沉默
                for a in all_agents:
                    if a != speaker:
                        a.mark_silent()

                await self._broadcast_expert_status(speaker, "idle", db)

                # === 3. Observer 分析 ===
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

            return True

    async def pause(self):
        self._paused.clear()

    async def resume(self):
        self._paused.set()

    async def stop(self):
        self._running = False
        self._paused.set()

    def is_running(self) -> bool:
        return self._running

    # ── Internal helpers ──

    async def _broadcast_expert_status(self, agent, status: str, db: AsyncSession):
        """广播专家状态 + 写入 DB 日志"""
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
        seq_result = await db.execute(
            select(func.max(Utterance.sequence_num)).where(
                Utterance.discussion_id == self.discussion_id
            )
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

    async def _load_transcript(self, db: AsyncSession) -> list[dict]:
        """从 DB 加载当前讨论的完整发言记录"""
        result = await db.execute(
            select(Utterance)
            .where(Utterance.discussion_id == self.discussion_id)
            .order_by(Utterance.sequence_num)
        )
        utterances = result.scalars().all()
        # 需要 eager load panel_member
        transcript = []
        for u in utterances:
            # panel_member is lazy loaded — 重新查询
            member = await db.get(PanelMember, u.panel_member_id)
            transcript.append({
                "id": u.id,
                "panel_member_id": u.panel_member_id,
                "member_name": member.name if member else "Unknown",
                "member_title": member.title if member else "",
                "member_color": member.color if member else "#000000",
                "content": u.content,
                "utterance_type": u.utterance_type,
                "sequence_num": u.sequence_num,
                "round_num": u.round_num,
                "created_at": u.created_at,
            })
        return transcript

    async def _load_consensus(self, db: AsyncSession) -> list[dict]:
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
        """Format a Utterance ORM object into the WS event dict"""
        return {
            "utterance_id": u.id,
            "member_id": u.panel_member_id,
            "member_name": "",
            "member_title": "",
            "member_color": "",
            "content": u.content,
            "utterance_type": u.utterance_type,
            "sequence_num": u.sequence_num,
            "round_num": u.round_num,
            "created_at": u.created_at,
        }

    async def _end_discussion(self, db: AsyncSession, d: Discussion, host: HostAgent, reason: str):
        """结束讨论：生成主持人总结 + 广播"""
        transcript = await self._load_transcript(db)

        # 主持人总结
        summary_text = ""
        async for token in host.generate_summary(transcript, d.topic):
            summary_text += token
            await self.ws.broadcast(self.discussion_id, {
                "type": "utterance_token",
                "data": {
                    "utterance_id": ":summary:", "member_id": host.member_id,
                    "member_name": host.name, "member_title": host.title,
                    "member_color": host.color, "token": token,
                    "sequence_num": len(transcript) + 1, "round_num": d.current_round + 1,
                    "is_first": (summary_text == token), "is_last": False,
                },
            })

        if summary_text:
            u = await self._save_utterance(db, host, summary_text, "summary", d.current_round + 1)
            await self.ws.broadcast(self.discussion_id, {
                "type": "utterance_complete",
                "data": self._format_utterance(u),
            })

        # 更新状态
        d.status = "ended"
        d.ended_at = _now()
        await db.commit()

        # 统计
        count_result = await db.execute(
            select(func.count(Utterance.id)).where(Utterance.discussion_id == self.discussion_id)
        )
        total = count_result.scalar() or 0

        await self.ws.broadcast(self.discussion_id, {
            "type": "discussion_ended",
            "data": {
                "discussion_id": self.discussion_id,
                "end_reason": reason,
                "total_rounds": d.current_round,
                "total_utterances": total,
                "ended_at": d.ended_at,
            },
        })

        self._running = False
