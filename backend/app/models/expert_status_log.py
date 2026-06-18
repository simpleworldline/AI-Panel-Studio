"""ExpertStatusLog 模型 — 对齐 DATABASE_DESIGN.md §2.5"""

from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, Float, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class ExpertStatusLog(Base):
    __tablename__ = "expert_status_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    discussion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("discussions.id"), nullable=False,
    )
    panel_member_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("panel_members.id"), nullable=False,
    )
    status: Mapped[str] = mapped_column(String(11), nullable=False)
    focus_summary: Mapped[str | None] = mapped_column(String(300), nullable=True, default=None)
    desire_value: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    recorded_at: Mapped[str] = mapped_column(
        String(25), nullable=False,
        default=lambda: datetime.now(timezone.utc).isoformat(),
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('idle', 'preparing', 'speaking')",
            name="ck_expert_status_logs_status",
        ),
    )
