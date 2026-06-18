"""DiscussionRunner — 讨论运行引擎（生命周期 + Agent 编排 + 事件总线）

Agent-Mediator 模式：
- 每个角色（Host/Expert/Observer）是独立 Agent
- Scheduler 负责冲突仲裁（欲望值→时间→随机，主持人同分优先）
- Runner 管理讨论生命周期并协调 WebSocket 广播
"""

import asyncio
import json
import logging
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

logger = logging.getLogger("discussion_runner")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class DiscussionRunner:
    """讨论运行引擎 — 管理讨论生命周期 + Agent 编排

    每个 Running 讨论在内存中有一个 Runner 实例。
    通过 asyncio.Event 实现 pause/resume 控制。
    禁用机械轮替：每轮由 Scheduler 按欲望值选择发言者。
    """

    def __init__(self, discussion_id: str, ws_manager):
        self.discussion_id = discussion_id
        self.ws = ws_manager
        self.scheduler = Scheduler()
        self.observer = ObserverAgent()
        self._paused = asyncio.Event()
        self._paused.set()          # 初始为运行状态（set = 不阻塞 wait）
        self._running = False
        self._task: asyncio.Task | None = None  # 保持后台任务引用

    async def run(self, session_factory: async_sessionmaker) -> bool:
        """启动讨论主循环 — 后台任务，运行直到讨论结束或被停止"""
        self._running = True
        self._paused.set()
        logger.info(f"[{self.discussion_id[:8]}] DiscussionRunner started")

        try:
            async with session_factory() as db:
                # 注意：SQLAlchemy async session 内所有操作必须在同一 async with 块内
                # 不能通过 await db.refresh() 访问 lazy-loaded relationship
                d = await db.get(Discussion, self.discussion_id)
                if d is None or d.status != "live":
                    logger.warning(f"[{self.discussion_id[:8]}] Discussion not found or not live")
                    return False

                # === 加载数据（全部在此 session 内） ===
                host, experts = await self._load_agents(db)
                if host is None:
                    logger.error(f"[{self.discussion_id[:8]}] No host found")
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
                        "data": self._format_utterance(u, host),
                    })
                await self._broadcast_expert_status(host, "idle", db)
                await db.commit()
                logger.info(f"[{self.discussion_id[:8]}] Opening done ({len(opening_text)} chars)")

                # === 2. 主发言循环 ===
                round_count = 0
                while self._running and round_count < 100:  # 安全上限
                    # 暂停等待
                    await self._paused.wait()

                    # 检查外部状态变更
                    await db.refresh(d)
                    if d.status not in ("live",):
                        break

                    # 结束条件
                    if d.max_rounds and d.current_round >= d.max_rounds:
                        logger.info(f"[{self.discussion_id[:8]}] Max rounds reached ({d.max_rounds})")
                        await self._end_discussion(db, d, host, "max_rounds")
                        break

                    # 加载最新 transcript
                    transcript = await self._load_transcript(db)
                    all_agents: list = [host] + experts

                    # 各 Agent 计算发言欲望值
                    for agent in all_agents:
                        await agent.prepare(transcript, d.topic)
                        await self._broadcast_expert_status(agent, "preparing", db)

                    # Scheduler 选出发言者（欲望值→时间→随机，主持人同分优先）
                    speaker = await self.scheduler.select_speaker(all_agents)
                    if speaker is None:
                        # 无 Agent 欲望值达到阈值，短暂等待后重试
                        for a in all_agents:
                            await self._broadcast_expert_status(a, "idle", db)
                        await asyncio.sleep(0.5)
                        continue

                    # 生成发言（流式推送）
                    await self._broadcast_expert_status(speaker, "speaking", db)
                    accumulated = ""
                    utterance_id = str(uuid.uuid4())
                    next_seq = len(transcript) + 1
                    new_round = d.current_round + 1

                    async for token in speaker.generate_utterance(transcript, d.topic):
                        accumulated += token
                        await self.ws.broadcast(self.discussion_id, {
                            "type": "utterance_token",
                            "data": {
                                "utterance_id": utterance_id, "member_id": speaker.member_id,
                                "member_name": speaker.name, "member_title": speaker.title,
                                "member_color": speaker.color, "token": token,
                                "sequence_num": next_seq, "round_num": new_round,
                                "is_first": (accumulated == token), "is_last": False,
                            },
                        })

                    if accumulated:
                        u = await self._save_utterance(db, speaker, accumulated, "statement", new_round)
                        await self.ws.broadcast(self.discussion_id, {
                            "type": "utterance_complete",
                            "data": self._format_utterance(u, speaker),
                        })
                        speaker.mark_spoke()
                        logger.info(f"[{self.discussion_id[:8]}] Round {new_round}: {speaker.name} spoke ({len(accumulated)} chars)")

                    # 其他 Agent 标记本轮沉默
                    for a in all_agents:
                        if a != speaker:
                            a.mark_silent()

                    await self._broadcast_expert_status(speaker, "idle", db)

                    # === 3. Observer 分析共识/分歧 ===
                    latest = self._format_utterance(u, speaker) if accumulated else None
                    if latest:
                        existing = await self._load_consensus(db)
                        analysis = await self.observer.analyze(transcript, latest, existing)
                        if analysis:
                            await self._save_consensus(db, analysis)
                            await self.ws.broadcast(self.discussion_id, {
                                "type": "consensus_update",
                                "data": analysis,
                            })
                            logger.info(f"[{self.discussion_id[:8]}] Consensus: {analysis.get('action', 'none')}")

                    # 轮次递增
                    d.current_round += 1
                    round_count += 1
                    await db.commit()

            # 如果 while 循环正常结束（非 stop 触发），调用结束流程
            if self._running:
                await self._end_discussion_with_db(d, host)

        except Exception as e:
            logger.exception(f"[{self.discussion_id[:8]}] Runner crashed: {e}")
        finally:
            self._running = False
            logger.info(f"[{self.discussion_id[:8]}] DiscussionRunner stopped")

        return True

    async def pause(self):
        """暂停发言循环"""
        self._paused.clear()

    async def resume(self):
        """继续发言循环"""
        self._paused.set()

    async def stop(self):
        """停止 Runner"""
        self._running = False
        self._paused.set()  # 解除可能的阻塞

    def is_running(self) -> bool:
        return self._running

    # ──────────────────────────────────────────────
    # Internal helpers (all must run within session)
    # ──────────────────────────────────────────────

    async def _load_agents(self, db: AsyncSession):
        """从 DB 加载主持人 + 专家 Agent"""
        result = await db.execute(
            select(PanelMember)
            .where(PanelMember.discussion_id == self.discussion_id)
            .order_by(PanelMember.sort_order)
        )
        members = result.scalars().all()
        host, experts = None, []
        for m in members:
            if m.role == "host":
                host = HostAgent(m.id, m.name, m.title, m.stance, m.color)
            else:
                experts.append(ExpertAgent(m.id, m.name, m.title, m.stance, m.color))
        return host, experts

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
        """从 DB 加载当前讨论的完整 transcript（含发言人信息）"""
        result = await db.execute(
            select(Utterance)
            .where(Utterance.discussion_id == self.discussion_id)
            .order_by(Utterance.sequence_num)
        )
        utterances = result.scalars().all()
        # 批量加载 PanelMember 避免 N+1
        member_ids = {u.panel_member_id for u in utterances}
        members_map = {}
        if member_ids:
            member_result = await db.execute(
                select(PanelMember).where(PanelMember.id.in_(member_ids))
            )
            for m in member_result.scalars().all():
                members_map[m.id] = m

        transcript = []
        for u in utterances:
            m = members_map.get(u.panel_member_id)
            transcript.append({
                "id": u.id, "panel_member_id": u.panel_member_id,
                "member_name": m.name if m else "Unknown",
                "member_title": m.title if m else "",
                "member_color": m.color if m else "#000",
                "content": u.content, "utterance_type": u.utterance_type,
                "sequence_num": u.sequence_num, "round_num": u.round_num,
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

    def _format_utterance(self, u: Utterance, agent=None) -> dict:
        """Format Utterance ORM object into WS event dict"""
        return {
            "utterance_id": u.id,
            "member_id": u.panel_member_id,
            "member_name": agent.name if agent else "",
            "member_title": agent.title if agent else "",
            "member_color": agent.color if agent else "",
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
                "data": self._format_utterance(u, host),
            })

        d.status = "ended"
        d.ended_at = _now()
        await db.commit()

        count_result = await db.execute(
            select(func.count(Utterance.id)).where(Utterance.discussion_id == self.discussion_id)
        )
        total = count_result.scalar() or 0

        await self.ws.broadcast(self.discussion_id, {
            "type": "discussion_ended",
            "data": {
                "discussion_id": self.discussion_id, "end_reason": reason,
                "total_rounds": d.current_round, "total_utterances": total,
                "ended_at": d.ended_at,
            },
        })

        self._running = False
        logger.info(f"[{self.discussion_id[:8]}] Discussion ended: {reason}")

    async def _end_discussion_with_db(self, d, host):
        """在已有 session 外部调用 end 的 fallback（runner 无 session 时）"""
        from app.db.database import async_session_factory
        async with async_session_factory() as db:
            d2 = await db.get(Discussion, self.discussion_id)
            if d2:
                d2.status = "ended"
                d2.ended_at = _now()
                await db.commit()
        await self.ws.broadcast(self.discussion_id, {
            "type": "discussion_ended",
            "data": {
                "discussion_id": self.discussion_id, "end_reason": "host_decided",
                "total_rounds": d.current_round if d else 0,
                "total_utterances": 0, "ended_at": _now(),
            },
        })
        self._running = False
