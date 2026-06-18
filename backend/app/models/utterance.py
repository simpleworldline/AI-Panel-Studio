"""DATABASE_DESIGN.md §2.3 — utterances 表"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Utterance(Base):
    __tablename__ = "utterances"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    discussion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("discussions.id", ondelete="CASCADE"), nullable=False
    )
    panel_member_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("panel_members.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    utterance_type: Mapped[str] = mapped_column(String(12), nullable=False)
    round_num: Mapped[int] = mapped_column(Integer, nullable=False)
    sequence_num: Mapped[int] = mapped_column(Integer, nullable=False)
    is_streaming: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(
        String(25),
        nullable=False,
        default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    __table_args__ = (
        CheckConstraint(
            "utterance_type IN ('opening', 'statement', 'rebuttal', 'supplement', 'question', 'summary')",
            name="ck_utterance_type",
        ),
    )

    # Relationships
    discussion = relationship("Discussion", back_populates="utterances")
    panel_member = relationship("PanelMember", back_populates="utterances")
