"""DATABASE_DESIGN.md §2.2 — panel_members 表"""

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class PanelMember(Base):
    __tablename__ = "panel_members"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    discussion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("discussions.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(6), nullable=False)
    stance: Mapped[str] = mapped_column(String(200), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#3B82F6")
    avatar_prompt: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("role IN ('host', 'expert')", name="ck_panel_member_role"),
        CheckConstraint("color LIKE '#______'", name="ck_panel_member_color"),
        Index(
            "uq_panel_member_disc_role",
            "discussion_id",
            unique=True,
            sqlite_where=text("role='host'"),
        ),
    )

    # Relationships
    discussion = relationship("Discussion", back_populates="panel_members")
    utterances = relationship("Utterance", back_populates="panel_member", cascade="all, delete-orphan")
    expert_status_logs = relationship("ExpertStatusLog", back_populates="panel_member", cascade="all, delete-orphan")
