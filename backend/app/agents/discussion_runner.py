"""DiscussionRunner — utterance-count-based continuous debate.

No rounds. Agents speak in a debate window: one speaks → rebuttals/responses
follow naturally until no one responds. The debate window then restarts.
Discussion ends when total utterances reach max_utterances or user ends.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

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

    def __init__(self, discussion_id: str, ws_manager):
        self.discussion_id = discussion_id
        self.ws = ws_manager
        self.scheduler = Scheduler()
        self.observer = ObserverAgent()
        self._paused = asyncio.Event()
        self._paused.set()
        self._force_step = asyncio.Event()
        self._force_step.clear()
        self._stopped = asyncio.Event()
        self._stopped.clear()

    async def run(self, session_factory: async_sessionmaker) -> bool:
        for _ in range(5):
            async with session_factory() as db:
                d = await db.get(Discussion, self.discussion_id)
                if d and d.status == "live":
                    break
            await asyncio.sleep(0.5)
        else:
            logger.warning(f"[{self.discussion_id[:8]}] never became live")
            return False

        try:
            # ── Opening ──
            async with session_factory() as db:
                d, host, experts = await self._init_agents(db)
                if d is None or host is None:
                    return False
                opening = await self._agent_speak(db, host, [], d.topic, "opening")
                if opening:
                    await db.commit()

            transcript = [opening] if opening else []

            # ── Continuous debate ──
            while not self._stopped.is_set():
                # pause / force-step wait
                if not self._paused.is_set():
                    await asyncio.wait(
                        [asyncio.create_task(self._paused.wait()),
                         asyncio.create_task(self._force_step.wait())],
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    self._force_step.clear()
                    if self._stopped.is_set():
                        break
                    continue

                self._force_step.clear()
                if self._stopped.is_set():
                    break

                # fresh session each debate cycle
                async with session_factory() as db:
                    d2 = await db.get(Discussion, self.discussion_id)
                    if d2 is None or d2.status not in ("live",):
                        break

                    _, host, experts = await self._init_agents(db)
                    if host is None:
                        break

                    transcript = await self._load_transcript(db)
                    total = len(transcript)

                    # ── End condition: utterance count ──
                    max_utterances = d2.max_rounds or 15   # default 15 utterances
                    if total >= max_utterances:
                        await self._end_discussion(db, d2, host, "max_utterances")
                        break

                    all_agents = [host] + experts

                    # ── Debate window: back-and-forth until silence ──
                    steps = 0
                    max_steps = 4          # 1 initial → 1 rebut → 1 reply → 1 host question max
                    last_speaker_id = None

                    while steps < max_steps and not self._stopped.is_set():
                        for agent in all_agents:
                            agent._desire = await agent.calculate_desire(transcript, d2.topic)
                            await self._broadcast(db, agent, "preparing")

                        candidates = all_agents if last_speaker_id is None else [
                            a for a in all_agents if a.member_id != last_speaker_id
                        ]

                        speaker = await self.scheduler.select_speaker(candidates)
                        if speaker is None:
                            # no one wants to speak → end this window
                            for a in all_agents:
                                await self._broadcast(db, a, "idle")
                            break

                        utype = "question" if (speaker.__class__.__name__ == "HostAgent" and steps == 0) else "statement"

                        utterance = await self._agent_speak(db, speaker, transcript, d2.topic, utype)

                        if utterance:
                            last_speaker_id = speaker.member_id
                            speaker.mark_spoke()
                            for a in all_agents:
                                if a != speaker:
                                    a.mark_silent()
                            transcript.append(utterance)

                            # Observer
                            existing = await self._load_consensus(db)
                            analysis = await self.observer.analyze(transcript, utterance, existing)
                            if analysis:
                                consensus_db = await self._save_consensus(db, analysis)
                                await self._broadcast_raw({
                                    "type": "consensus_update",
                                    "data": {
                                        "action": analysis.get("action", "created"),
                                        "record": {
                                            "id": consensus_db.id,
                                            "type": analysis.get("type", "consensus"),
                                            "title": analysis.get("title", ""),
                                            "description": analysis.get("description", ""),
                                            "source_utterance_ids": (
                                                json.loads(consensus_db.source_utterance_ids)
                                                if consensus_db.source_utterance_ids else []
                                            ),
                                            "confidence": analysis.get("confidence", 0.5),
                                            "is_resolved": bool(consensus_db.is_resolved),
                                            "round_num": analysis.get("round_num", 0),
                                        },
                                    },
                                })
                            steps += 1

                        await self._broadcast(db, speaker, "idle")
                        await db.commit()

                        # pause/stop after each utterance
                        if self._stopped.is_set():
                            for a in all_agents:
                                await self._broadcast(db, a, "idle")
                            await self._end_discussion(db, d2, host, "user_ended")
                            return True
                        if not self._paused.is_set():
                            for a in all_agents:
                                await self._broadcast(db, a, "idle")
                            logger.info(f"[{self.discussion_id[:8]}] paused")
                            break

                    # Update utterance counter in DB
                    await db.refresh(d2)
                    total_now_result = await db.execute(
                        select(func.count(Utterance.id)).where(
                            Utterance.discussion_id == self.discussion_id
                        )
                    )
                    new_total = total_now_result.scalar() or 0
                    d2.current_round = new_total   # reuse column as utterance counter
                    await db.commit()

            # ── Auto-end ──
            async with session_factory() as db:
                d3 = await db.get(Discussion, self.discussion_id)
                if d3 and d3.status not in ("ended",):
                    _, host, _ = await self._init_agents(db)
                    if host:
                        await self._end_discussion(db, d3, host, "host_decided")

        except Exception as e:
            logger.exception(f"[{self.discussion_id[:8]}] crashed: {e}")
        finally:
            self._stopped.set()
            logger.info(f"[{self.discussion_id[:8]}] stopped")
        return True

    # ─── Public API ───
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

    # ─── Internal ───

    async def _init_agents(self, db: AsyncSession):
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

    async def _agent_speak(self, db: AsyncSession, agent, transcript, topic, utype) -> dict | None:
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
                    "sequence_num": len(transcript) + 1, "round_num": 0,
                    "is_first": (text == token), "is_last": False,
                },
            })
        if not text:
            return None
        seq_result = await db.execute(
            select(func.max(Utterance.sequence_num)).where(
                Utterance.discussion_id == self.discussion_id
            )
        )
        max_seq = seq_result.scalar() or 0
        u = Utterance(
            id=str(uuid.uuid4()), discussion_id=self.discussion_id,
            panel_member_id=agent.member_id, content=text,
            utterance_type=utype, round_num=0, sequence_num=max_seq + 1,
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
        transcript = await self._load_transcript(db)
        summary = ""
        async for token in host.generate_summary(transcript, d.topic):
            summary += token
            await self._broadcast_raw({
                "type": "utterance_token",
                "data": {
                    "utterance_id": ":summary:", "member_id": host.member_id,
                    "member_name": host.name, "member_title": host.title,
                    "member_color": host.color, "token": token,
                    "sequence_num": len(transcript) + 1, "round_num": 0,
                    "is_first": (summary == token), "is_last": False,
                },
            })
        if summary:
            u = Utterance(id=str(uuid.uuid4()), discussion_id=self.discussion_id,
                         panel_member_id=host.member_id, content=summary,
                         utterance_type="summary", round_num=0,
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
                "total_rounds": total_utterances, "total_utterances": total_utterances,
                "ended_at": d.ended_at,
            },
        })
        logger.info(f"[{self.discussion_id[:8]}] ended: {reason}")

    async def _broadcast(self, db: AsyncSession, agent, status: str):
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
        try:
            await self.ws.broadcast(self.discussion_id, event)
        except Exception:
            pass

    async def _load_transcript(self, db: AsyncSession) -> list[dict]:
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
        return [
            {
                "id": u.id, "panel_member_id": u.panel_member_id,
                "member_name": member_map[u.panel_member_id].name if u.panel_member_id in member_map else "Unknown",
                "member_title": member_map[u.panel_member_id].title if u.panel_member_id in member_map else "",
                "member_color": member_map[u.panel_member_id].color if u.panel_member_id in member_map else "#000",
                "content": u.content, "utterance_type": u.utterance_type,
                "sequence_num": u.sequence_num, "round_num": u.round_num,
                "created_at": u.created_at,
            }
            for u in utterances
        ]

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

    async def _save_consensus(self, db: AsyncSession, analysis: dict) -> ConsensusDisagreement:
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
        return cd

    def _fmt_utterance(self, u, agent) -> dict:
        return {
            "utterance_id": u.id, "member_id": u.panel_member_id,
            "member_name": agent.name, "member_title": agent.title,
            "member_color": agent.color, "content": u.content,
            "utterance_type": u.utterance_type,
            "sequence_num": u.sequence_num, "round_num": u.round_num,
            "created_at": u.created_at,
        }
