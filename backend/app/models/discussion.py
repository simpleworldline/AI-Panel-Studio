"""Discussion 模型 — 对齐 DATABASE_DESIGN.md §2.1"""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Discussion(Base):
    __tablename__ = "discussions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    expert_count: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    max_rounds: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="pending")
    creator_session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    current_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rounds_without_consensus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    auto_end_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    created_at: Mapped[str] = mapped_column(
        String(25), nullable=False,
        default=lambda: datetime.now(timezone.utc).isoformat(),
    )
    ended_at: Mapped[str | None] = mapped_column(String(25), nullable=True, default=None)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'live', 'paused', 'ended')",
            name="ck_discussions_status",
        ),
        CheckConstraint(
            "expert_count BETWEEN 2 AND 8",
            name="ck_discussions_expert_count",
        ),
    )
