"""DATABASE_DESIGN.md §2.4 — consensus_disagreements 表"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ConsensusDisagreement(Base):
    __tablename__ = "consensus_disagreements"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    discussion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("discussions.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(13), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    source_utterance_ids: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_resolved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    round_num: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[str] = mapped_column(
        String(25),
        nullable=False,
        default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    updated_at: Mapped[str] = mapped_column(
        String(25),
        nullable=False,
        default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    __table_args__ = (
        CheckConstraint("type IN ('consensus', 'disagreement')", name="ck_consensus_type"),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="ck_consensus_confidence"),
    )

    # Relationships
    discussion = relationship("Discussion", back_populates="consensus_disagreements")
