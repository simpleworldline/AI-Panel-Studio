"""Utterance 模型 — 对齐 DATABASE_DESIGN.md §2.3"""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Utterance(Base):
    __tablename__ = "utterances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    discussion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("discussions.id"), nullable=False,
    )
    panel_member_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("panel_members.id"), nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    utterance_type: Mapped[str] = mapped_column(String(12), nullable=False)
    round_num: Mapped[int] = mapped_column(Integer, nullable=False)
    sequence_num: Mapped[int] = mapped_column(Integer, nullable=False)
    is_streaming: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(
        String(25), nullable=False,
        default=lambda: datetime.now(timezone.utc).isoformat(),
    )

    __table_args__ = (
        CheckConstraint(
            "utterance_type IN ('opening', 'statement', 'rebuttal', 'supplement', 'question', 'summary')",
            name="ck_utterances_type",
        ),
    )
