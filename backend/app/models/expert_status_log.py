"""DATABASE_DESIGN.md §2.5 — expert_status_logs 表"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class ExpertStatusLog(Base):
    __tablename__ = "expert_status_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    discussion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("discussions.id", ondelete="CASCADE"), nullable=False
    )
    panel_member_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("panel_members.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(11), nullable=False)
    focus_summary: Mapped[str | None] = mapped_column(String(300), nullable=True, default=None)
    desire_value: Mapped[float | None] = mapped_column(Float, nullable=True, default=None)
    recorded_at: Mapped[str] = mapped_column(
        String(25),
        nullable=False,
        default=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    __table_args__ = (
        CheckConstraint("status IN ('idle', 'preparing', 'speaking')", name="ck_expert_status"),
    )

    # Relationships
    discussion = relationship("Discussion", back_populates="expert_status_logs")
    panel_member = relationship("PanelMember", back_populates="expert_status_logs")
