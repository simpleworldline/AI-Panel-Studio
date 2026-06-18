"""DiscussionRunner — Agent-Mediator pattern with short-lived DB sessions.

Avoids SQLite write contention by opening/closing a session per round.
pause/resume/end are signaled through Events, the runner acts on them
inside its own session.
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
    """Discussion lifecycle engine.

    Each running discussion has one Runner instance in memory.
    Uses short-lived DB sessions to avoid SQLite write contention.
    Controlled by asyncio.Event for pause/resume/force-step/stop.
    """

    def __init__(self, discussion_id: str, ws_manager):
        self.discussion_id = discussion_id
        self.ws = ws_manager
        self.scheduler = Scheduler()
        self.observer = ObserverAgent()
        # Control events
        self._paused = asyncio.Event()
        self._paused.set()                # initially running
        self._force_step = asyncio.Event()
        self._force_step.clear()
        self._stopped = asyncio.Event()
        self._stopped.clear()
        self._session_factory: async_sessionmaker | None = None

    async def run(self, session_factory: async_sessionmaker) -> bool:
        """Main discussion loop (runs as background task)."""
        self._session_factory = session_factory

        # Retry until discussion status=live (start endpoint may not have committed yet)
        for _ in range(5):
            async with session_factory() as db:
                d = await db.get(Discussion, self.discussion_id)
                if d and d.status == "live":
                    break
            await asyncio.sleep(0.5)
        else:
            logger.warning(f"[{self.discussion_id[:8]}] status never became live, giving up")
            return False

        try:
            # === 1. Opening statement ===
            async with session_factory() as db:
                d, host, experts = await self._init_round(db)
                if d is None or host is None:
                    return False

                opening = await self._agent_speak(db, host, [], d.topic, "opening", 0)
                if opening:
                    await db.commit()

            # === 2. Main loop ===
            transcript = [opening] if opening else []
            round_count = 0

            while not self._stopped.is_set() and round_count < 100:
                # If paused, wait for resume or force_step (DB already updated by REST)
                if not self._paused.is_set():
                    await asyncio.wait(
                        [asyncio.create_task(self._paused.wait()),
                         asyncio.create_task(self._force_step.wait())],
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    self._force_step.clear()
                    continue

                self._force_step.clear()

                if self._stopped.is_set():
                    break

                async with session_factory() as db:
                    # Refresh state
                    d2 = await db.get(Discussion, self.discussion_id)
                    if d2 is None or d2.status not in ("live",):
                        break

                    # Reload agents (they're stateless enough to recreate)
                    _, host, experts = await self._init_round(db)
                    if host is None:
                        break

                    # Reload transcript
                    transcript = await self._load_transcript(db)

                    # End conditions
                    if d2.status == "ended":
                        break
                    if d2.max_rounds and d2.current_round >= d2.max_rounds:
                        await self._end_discussion(db, d2, host, "max_rounds")
                        break

                    all_agents = [host] + experts

                    # Each agent calculates desire + broadcasts status
                    for agent in all_agents:
                        agent._desire = await agent.calculate_desire(transcript, d2.topic)
                        await self._broadcast(db, agent, "preparing")

                    # Scheduler picks speaker
                    speaker = await self.scheduler.select_speaker(all_agents)
                    if speaker is None:
                        for a in all_agents:
                            await self._broadcast(db, a, "idle")
                        await db.commit()
                        await asyncio.sleep(1)
                        continue

                    # Speak
                    utterance = await self._agent_speak(
                        db, speaker, transcript, d2.topic,
                        "statement", d2.current_round + 1,
                    )
                    if utterance:
                        speaker.mark_spoke()
                        for a in all_agents:
                            if a != speaker:
                                a.mark_silent()

                        # Observer analysis
                        latest = self._fmt_utterance(utterance, speaker)
                        existing = await self._load_consensus(db)
                        analysis = await self.observer.analyze(transcript, latest, existing)
                        if analysis:
                            await self._save_consensus(db, analysis)
                            await self._broadcast_raw({
                                "type": "consensus_update", "data": analysis,
                            })
                            logger.info(f"[{self.discussion_id[:8]}] consensus: {analysis.get('action')}")

                        transcript.append(self._fmt_utterance(utterance, speaker))

                    await self._broadcast(db, speaker, "idle")
                    d2.current_round += 1
                    round_count += 1
                    await db.commit()

            # === 3. End ===
            async with session_factory() as db:
                d3 = await db.get(Discussion, self.discussion_id)
                if d3 and d3.status not in ("ended",):
                    _, host, _ = await self._init_round(db)
                    if host:
                        await self._end_discussion(db, d3, host, "host_decided")

        except Exception as e:
            logger.exception(f"[{self.discussion_id[:8]}] crashed: {e}")
        finally:
            self._stopped.set()
            logger.info(f"[{self.discussion_id[:8]}] stopped")
        return True

    # ─── Public control API ───
    def pause(self):
        self._paused.clear()

    def resume(self):
        self._paused.set()

    def force_step(self):
        self._force_step.set()

    def stop(self):
        self._stopped.set()
        self._paused.set()
        self._force_step.set()

    def is_running(self) -> bool:
        return not self._stopped.is_set()

    # ─── Internal helpers ───

    async def _init_round(self, db: AsyncSession):
        """Load discussion + agents within current session."""
        d = await db.get(Discussion, self.discussion_id)
        if d is None:
            return None, None, None
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
        return d, host, experts

    async def _agent_speak(self, db: AsyncSession, agent, transcript, topic, utype, round_num) -> dict | None:
        """Stream agent utterance → WS + DB, return formatted dict or None."""
        await self._broadcast(db, agent, "speaking")
        text = ""
        async for token in agent.generate_utterance(transcript, topic):
            text += token
            await self._broadcast_raw({
                "type": "utterance_token",
                "data": {
                    "utterance_id": f":{utype}:", "member_id": agent.member_id,
                    "member_name": agent.name, "member_title": agent.title,
                    "member_color": agent.color, "token": token,
                    "sequence_num": len(transcript) + 1, "round_num": round_num,
                    "is_first": (text == token), "is_last": False,
                },
            })
        if not text:
            return None
        # Save in DB
        seq_result = await db.execute(
            select(func.max(Utterance.sequence_num)).where(
                Utterance.discussion_id == self.discussion_id
            )
        )
        max_seq = seq_result.scalar() or 0
        u = Utterance(
            id=str(uuid.uuid4()), discussion_id=self.discussion_id,
            panel_member_id=agent.member_id, content=text,
            utterance_type=utype, round_num=round_num, sequence_num=max_seq + 1,
        )
        db.add(u)
        await db.flush()
        await db.refresh(u)
        await self._broadcast_raw({
            "type": "utterance_complete",
            "data": self._fmt_utterance(u, agent),
        })
        logger.info(f"[{self.discussion_id[:8]}] {agent.name}({utype}): {text[:60]}...")
        return self._fmt_utterance(u, agent)

    async def _end_discussion(self, db: AsyncSession, d, host, reason: str):
        """Generate host summary, mark ended, broadcast."""
        transcript = await self._load_transcript(db)
        # Summary
        summary = ""
        async for token in host.generate_summary(transcript, d.topic):
            summary += token
            await self._broadcast_raw({
                "type": "utterance_token",
                "data": {
                    "utterance_id": ":summary:", "member_id": host.member_id,
                    "member_name": host.name, "member_title": host.title,
                    "member_color": host.color, "token": token,
                    "sequence_num": len(transcript) + 1, "round_num": d.current_round + 1,
                    "is_first": (summary == token), "is_last": False,
                },
            })
        if summary:
            u = Utterance(id=str(uuid.uuid4()), discussion_id=self.discussion_id,
                         panel_member_id=host.member_id, content=summary,
                         utterance_type="summary", round_num=d.current_round + 1,
                         sequence_num=len(transcript) + 1)
            db.add(u)
            await db.flush()
            await self._broadcast_raw({
                "type": "utterance_complete",
                "data": self._fmt_utterance(u, host),
            })

        d.status = "ended"
        d.ended_at = _now()
        await db.commit()

        total = await db.execute(
            select(func.count(Utterance.id)).where(Utterance.discussion_id == self.discussion_id)
        )
        total_utterances = total.scalar() or 0

        await self._broadcast_raw({
            "type": "discussion_ended",
            "data": {
                "discussion_id": self.discussion_id, "end_reason": reason,
                "total_rounds": d.current_round, "total_utterances": total_utterances,
                "ended_at": d.ended_at,
            },
        })
        logger.info(f"[{self.discussion_id[:8]}] ended: {reason}")

    async def _broadcast(self, db: AsyncSession, agent, status: str):
        """Broadcast expert status + save log."""
        log = ExpertStatusLog(
            id=str(uuid.uuid4()), discussion_id=self.discussion_id,
            panel_member_id=agent.member_id, status=status,
            focus_summary=agent.focus_summary, desire_value=agent.desire_value,
        )
        db.add(log)
        await db.flush()
        await self._broadcast_raw({
            "type": "expert_status",
            "data": {
                "member_id": agent.member_id, "member_name": agent.name,
                "member_color": agent.color, "status": status,
                "focus_summary": agent.focus_summary,
                "desire_value": agent.desire_value,
                "timestamp": log.recorded_at,
            },
        })

    async def _broadcast_raw(self, event: dict):
        """Send event to all connected WS clients."""
        try:
            await self.ws.broadcast(self.discussion_id, event)
        except Exception:
            pass

    async def _load_transcript(self, db: AsyncSession) -> list[dict]:
        """Load transcript with member names."""
        result = await db.execute(
            select(Utterance)
            .where(Utterance.discussion_id == self.discussion_id)
            .order_by(Utterance.sequence_num)
        )
        utterances = result.scalars().all()
        member_ids = {u.panel_member_id for u in utterances}
        member_map = {}
        if member_ids:
            m_result = await db.execute(
                select(PanelMember).where(PanelMember.id.in_(member_ids))
            )
            for m in m_result.scalars().all():
                member_map[m.id] = m
        transcript = []
        for u in utterances:
            m = member_map.get(u.panel_member_id)
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
        return [
            {"id": c.id, "type": c.type, "title": c.title,
             "description": c.description, "source_utterance_ids": c.source_utterance_ids,
             "confidence": c.confidence, "is_resolved": bool(c.is_resolved),
             "round_num": c.round_num}
            for c in result.scalars().all()
        ]

    async def _save_consensus(self, db: AsyncSession, analysis: dict):
        cd = ConsensusDisagreement(
            id=str(uuid.uuid4()), discussion_id=self.discussion_id,
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

    def _fmt_utterance(self, u, agent) -> dict:
        return {
            "utterance_id": u.id, "member_id": u.panel_member_id,
            "member_name": agent.name, "member_title": agent.title,
            "member_color": agent.color, "content": u.content,
            "utterance_type": u.utterance_type,
            "sequence_num": u.sequence_num, "round_num": u.round_num,
            "created_at": u.created_at,
        }
