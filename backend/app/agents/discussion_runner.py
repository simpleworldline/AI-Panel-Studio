"""DiscussionRunner — continuous debate with per-utterance sessions"""

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
        self._already_ended = False

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
            # === Opening ===
            async with session_factory() as db:
                d, host, experts = await self._init_agents(db)
                if d is None or host is None:
                    return False
                opening = await self._agent_speak(db, host, [], d.topic, "opening")
                if opening:
                    await db.commit()

            transcript = [opening] if opening else []

            # === Continuous debate ===
            while not self._stopped.is_set():
                if not self._paused.is_set():
                    async with session_factory() as db_p:
                        d_p = await db_p.get(Discussion, self.discussion_id)
                        if d_p and d_p.status == "live":
                            d_p.status = "paused"
                            await db_p.commit()
                    await asyncio.wait(
                        [asyncio.create_task(self._paused.wait()),
                         asyncio.create_task(self._force_step.wait())],
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    self._force_step.clear()
                    if self._stopped.is_set():
                        break
                    async with session_factory() as db_r:
                        d_r = await db_r.get(Discussion, self.discussion_id)
                        if d_r and d_r.status == "paused":
                            d_r.status = "live"
                            await db_r.commit()
                    continue

                self._force_step.clear()
                if self._stopped.is_set():
                    break

                # === Check end conditions ===
                async with session_factory() as db_check:
                    d2 = await db_check.get(Discussion, self.discussion_id)
                    if d2 is None or d2.status not in ("live",):
                        break
                    max_utterances = d2.max_rounds or 15
                    count_result = await db_check.execute(
                        select(func.count(Utterance.id)).where(
                            Utterance.discussion_id == self.discussion_id
                        )
                    )
                    total = count_result.scalar() or 0
                    d2.current_round = total
                    await db_check.commit()

                if total >= max_utterances:
                    async with session_factory() as db_end:
                        d_end = await db_end.get(Discussion, self.discussion_id)
                        if d_end and d_end.status not in ("ended",):
                            _, host_end, _ = await self._init_agents(db_end)
                            if host_end:
                                await self._end_discussion(db_end, d_end, host_end, "max_utterances")
                                self._already_ended = True
                    break

                # === Debate window ===
                steps = 0
                last_speaker_id = None
                parent_utterance_id = None

                while steps < 4 and not self._stopped.is_set():

                    async with session_factory() as db_step:
                        d_step = await db_step.get(Discussion, self.discussion_id)
                        if d_step is None or d_step.status not in ("live",):
                            break

                        _, host_step, experts_step = await self._init_agents(db_step)
                        if host_step is None:
                            break

                        transcript = await self._load_transcript(db_step)
                        all_agents_step = [host_step] + experts_step

                        for agent in all_agents_step:
                            agent._desire = await agent.calculate_desire(transcript, d_step.topic)
                            await self._broadcast(db_step, agent, "preparing")

                        candidates = all_agents_step if last_speaker_id is None else [
                            a for a in all_agents_step if a.member_id != last_speaker_id
                        ]

                        speaker = await self.scheduler.select_speaker(candidates)
                        if speaker is None:
                            if steps == 0:
                                host_step._desire = 1.0
                                await self._broadcast(db_step, host_step, "preparing")
                                utterance = await self._agent_speak(
                                    db_step, host_step, transcript, d_step.topic, "question")
                                if utterance:
                                    last_speaker_id = host_step.member_id
                                    transcript.append(utterance)
                                    steps += 1
                                    await self._broadcast(db_step, host_step, "idle")
                                    await db_step.commit()
                                    if self._stopped.is_set():
                                        await self._quick_end(db_step, d_step, "user_ended")
                                        self._already_ended = True
                                        return True
                                    if not self._paused.is_set():
                                        break
                                    continue
                            for a in all_agents_step:
                                await self._broadcast(db_step, a, "idle")
                            await db_step.commit()
                            break

                        utype = "question" if (speaker.__class__.__name__ == "HostAgent" and steps == 0) else "statement"
                        pid = None if steps == 0 else parent_utterance_id
                        utterance = await self._agent_speak(db_step, speaker, transcript, d_step.topic, utype, pid)

                        if utterance:
                            if parent_utterance_id is None:
                                parent_utterance_id = utterance.get("utterance_id")
                            last_speaker_id = speaker.member_id
                            speaker.mark_spoke()
                            for a in all_agents_step:
                                if a != speaker:
                                    a.mark_silent()
                            transcript.append(utterance)

                            existing = await self._load_consensus(db_step)
                            analysis = await self.observer.analyze(transcript, utterance, existing)
                            if analysis:
                                consensus_db = await self._save_consensus(db_step, analysis)
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

                        await self._broadcast(db_step, speaker, "idle")
                        await db_step.commit()

                        # User clicked end: immediate close, NO summary
                        if self._stopped.is_set():
                            for a in all_agents_step:
                                await self._broadcast(db_step, a, "idle")
                            await self._quick_end(db_step, d_step, "user_ended")
                            self._already_ended = True
                            return True
                        # User clicked pause: end this debate window
                        if not self._paused.is_set():
                            for a in all_agents_step:
                                await self._broadcast(db_step, a, "idle")
                            break

                # Update utterance counter
                if not self._stopped.is_set():
                    async with session_factory() as db_total:
                        d_total = await db_total.get(Discussion, self.discussion_id)
                        if d_total:
                            count = await db_total.execute(
                                select(func.count(Utterance.id)).where(
                                    Utterance.discussion_id == self.discussion_id
                                )
                            )
                            d_total.current_round = count.scalar() or 0
                            await db_total.commit()

            # === Auto-end: summary only for natural completion ===
            if not self._already_ended:
                async with session_factory() as db_final:
                    d_final = await db_final.get(Discussion, self.discussion_id)
                    if d_final and d_final.status not in ("ended",):
                        _, host_final, _ = await self._init_agents(db_final)
                        if host_final:
                            await self._end_discussion(db_final, d_final, host_final, "host_decided")
                            self._already_ended = True

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

    async def _agent_speak(self, db: AsyncSession, agent, transcript, topic, utype, parent_id=None) -> dict | None:
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
        fmt = self._fmt_utterance(u, agent)
        fmt["parent_utterance_id"] = parent_id
        await self._broadcast_raw({
            "type": "utterance_complete",
            "data": fmt,
        })
        logger.info(f"[{self.discussion_id[:8]}] {agent.name}({utype}): {text[:60]}...")
        return fmt

    async def _quick_end(self, db: AsyncSession, d, reason: str):
        """Immediate end — write DB + broadcast, no summary."""
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
        logger.info(f"[{self.discussion_id[:8]}] quick-ended: {reason}")

    async def _end_discussion(self, db: AsyncSession, d, host, reason: str):
        """Natural end — generate summary + mark ended + broadcast."""
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
