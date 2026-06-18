"""PanelMember 模型 — 对齐 DATABASE_DESIGN.md §2.2"""

from sqlalchemy import String, Integer, Text, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class PanelMember(Base):
    __tablename__ = "panel_members"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    discussion_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("discussions.id"), nullable=False,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(6), nullable=False)
    stance: Mapped[str] = mapped_column(String(200), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#3B82F6")
    avatar_prompt: Mapped[str | None] = mapped_column(String(500), nullable=True, default=None)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint(
            "role IN ('host', 'expert')",
            name="ck_panel_members_role",
        ),
    )
