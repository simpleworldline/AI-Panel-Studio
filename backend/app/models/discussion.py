"""DATABASE_DESIGN.md §2.1 — discussions 表"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Discussion(Base):
    __tablename__ = "discussions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    expert_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=4
    )
    max_rounds: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, default="pending"
    )
    creator_session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    current_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rounds_without_consensus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    auto_end_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    created_at: Mapped[str] = mapped_column(
        String(25),
        nullable=False,
        default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    ended_at: Mapped[str | None] = mapped_column(String(25), nullable=True, default=None)

    __table_args__ = (
        CheckConstraint("expert_count >= 2 AND expert_count <= 8", name="ck_expert_count"),
        CheckConstraint("status IN ('pending', 'live', 'paused', 'ended')", name="ck_discussion_status"),
    )

    # Relationships
    panel_members = relationship("PanelMember", back_populates="discussion", cascade="all, delete-orphan")
    utterances = relationship("Utterance", back_populates="discussion", cascade="all, delete-orphan")
    consensus_disagreements = relationship("ConsensusDisagreement", back_populates="discussion", cascade="all, delete-orphan")
    expert_status_logs = relationship("ExpertStatusLog", back_populates="discussion", cascade="all, delete-orphan")
