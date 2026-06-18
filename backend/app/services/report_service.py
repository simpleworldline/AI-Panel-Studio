"""ReportService — 讨论报告聚合"""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.discussion import Discussion
from app.models.panel_member import PanelMember
from app.models.utterance import Utterance
from app.models.consensus import ConsensusDisagreement


def _parse_source_ids(raw: str) -> list:
    """Parse source_utterance_ids from JSON string to list"""
    try:
        return json.loads(raw) if raw else []
    except (json.JSONDecodeError, TypeError):
        return []


class ReportService:

    @staticmethod
    async def generate_report(session: AsyncSession, discussion_id: str) -> dict | None:
        d = await session.get(Discussion, discussion_id)
        if d is None:
            return None

        # Panel
        panel_result = await session.execute(
            select(PanelMember).where(PanelMember.discussion_id == discussion_id).order_by(PanelMember.sort_order)
        )
        panel = [
            {"id": m.id, "name": m.name, "title": m.title, "role": m.role,
             "stance": m.stance, "color": m.color}
            for m in panel_result.scalars().all()
        ]

        # Transcript (eager load panel_member to avoid MissingGreenlet in production)
        utterance_result = await session.execute(
            select(Utterance)
            .where(Utterance.discussion_id == discussion_id)
            .options(selectinload(Utterance.panel_member))
            .order_by(Utterance.sequence_num)
        )
        transcript = [
            {
                "id": u.id,
                "panel_member_id": u.panel_member_id,
                "member_name": u.panel_member.name,
                "member_title": u.panel_member.title,
                "member_color": u.panel_member.color,
                "content": u.content,
                "utterance_type": u.utterance_type,
                "sequence_num": u.sequence_num,
                "round_num": u.round_num,
                "created_at": u.created_at,
            }
            for u in utterance_result.scalars().all()
        ]

        # Consensus & Disagreements
        cd_result = await session.execute(
            select(ConsensusDisagreement).where(
                ConsensusDisagreement.discussion_id == discussion_id
            ).order_by(ConsensusDisagreement.created_at)
        )
        all_cds = cd_result.scalars().all()
        consensus = [
            {"id": c.id, "type": "consensus", "title": c.title, "description": c.description,
             "source_utterance_ids": _parse_source_ids(c.source_utterance_ids), "confidence": c.confidence,
             "is_resolved": bool(c.is_resolved), "round_num": c.round_num}
            for c in all_cds if c.type == "consensus"
        ]
        disagreements = [
            {"id": c.id, "type": "disagreement", "title": c.title, "description": c.description,
             "source_utterance_ids": _parse_source_ids(c.source_utterance_ids), "confidence": c.confidence,
             "is_resolved": bool(c.is_resolved), "round_num": c.round_num}
            for c in all_cds if c.type == "disagreement"
        ]

        # Host summary = last utterance
        host_summary = None
        if transcript:
            last = transcript[-1]
            if last["utterance_type"] == "summary":
                host_summary = last["content"]

        return {
            "discussion_id": d.id,
            "topic": d.topic,
            "panel": panel,
            "transcript": transcript,
            "consensus": consensus,
            "disagreements": disagreements,
            "host_summary": host_summary or "",
        }
