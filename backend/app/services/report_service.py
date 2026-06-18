"""ReportService — 讨论报告聚合"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discussion import Discussion
from app.models.panel_member import PanelMember
from app.models.utterance import Utterance
from app.models.consensus import ConsensusDisagreement


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

        # Transcript
        utterance_result = await session.execute(
            select(Utterance).where(Utterance.discussion_id == discussion_id).order_by(Utterance.sequence_num)
        )
        transcript = [
            {
                "sequence_num": u.sequence_num, "member_name": u.panel_member.name,
                "member_title": u.panel_member.title, "member_color": u.panel_member.color,
                "content": u.content, "utterance_type": u.utterance_type,
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
            {"id": c.id, "title": c.title, "description": c.description,
             "source_utterance_ids": c.source_utterance_ids,
             "confidence": c.confidence, "round_num": c.round_num}
            for c in all_cds if c.type == "consensus"
        ]
        disagreements = [
            {"id": c.id, "title": c.title, "description": c.description,
             "source_utterance_ids": c.source_utterance_ids,
             "confidence": c.confidence, "is_resolved": bool(c.is_resolved),
             "round_num": c.round_num}
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
