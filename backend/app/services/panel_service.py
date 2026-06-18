"""PanelService — 嘉宾生成 + 编辑确认"""

import uuid
from typing import AsyncGenerator

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discussion import Discussion
from app.models.panel_member import PanelMember
from app.schemas.panel import PanelConfirmRequest


EXPERT_COLORS = ["#6366F1", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#06B6D4", "#F97316"]


class PanelService:

    @staticmethod
    async def generate_panel(
        session: AsyncSession,
        discussion_id: str,
        regenerate_member_id: str | None = None,
    ) -> dict:
        """生成嘉宾阵容（Mock 默认阵容，不调用 LLM）"""
        d = await session.get(Discussion, discussion_id)
        if d is None:
            raise ValueError("讨论不存在")

        # Default mock host
        host = {
            "name": "张明",
            "title": "AI伦理学家",
            "stance": "中立客观，擅长引导讨论",
            "color": "#6366F1",
            "avatar_prompt": None,
        }
        # Default mock experts
        expert_templates = [
            {"name": "李研究员", "title": "认知科学研究所高级研究员", "stance": "支持AI具备有限自我意识"},
            {"name": "王教授", "title": "计算机科学教授", "stance": "反对赋予AI自我意识，存在安全风险"},
            {"name": "陈博士", "title": "神经科学博士", "stance": "从生物学角度比较人类与AI意识"},
            {"name": "赵工程师", "title": "AI产品经理", "stance": "从产品实用角度讨论"},
        ]
        experts = []
        for i in range(min(d.expert_count, len(expert_templates))):
            t = expert_templates[i]
            experts.append({
                **t,
                "color": EXPERT_COLORS[(i + 1) % len(EXPERT_COLORS)],
                "avatar_prompt": None,
            })

        return {"host": host, "experts": experts}

    @staticmethod
    async def confirm_panel(
        session: AsyncSession,
        discussion_id: str,
        host: dict,
        experts: list[dict],
    ) -> dict:
        """确认并保存嘉宾阵容"""
        d = await session.get(Discussion, discussion_id)
        if d is None:
            raise ValueError("讨论不存在")
        if d.status != "pending":
            raise ValueError("阵容已确认不可修改")

        # 清除旧阵容
        result = await session.execute(
            select(PanelMember).where(PanelMember.discussion_id == discussion_id)
        )
        old_members = result.scalars().all()
        for m in old_members:
            await session.delete(m)
        await session.flush()

        members = []
        # Host
        h = PanelMember(
            id=str(uuid.uuid4()),
            discussion_id=discussion_id,
            name=host["name"],
            title=host["title"],
            role="host",
            stance=host.get("stance", ""),
            color=host.get("color", "#6366F1"),
            sort_order=0,
        )
        session.add(h)
        members.append(h)

        # Experts
        for i, expert in enumerate(experts):
            pm = PanelMember(
                id=str(uuid.uuid4()),
                discussion_id=discussion_id,
                name=expert["name"],
                title=expert["title"],
                role="expert",
                stance=expert.get("stance", ""),
                color=expert.get("color", EXPERT_COLORS[(i + 1) % len(EXPERT_COLORS)]),
                sort_order=i + 1,
            )
            session.add(pm)
            members.append(pm)

        await session.flush()

        members_response = [
            {
                "id": m.id, "name": m.name, "title": m.title,
                "role": m.role, "stance": m.stance, "color": m.color, "avatar_prompt": m.avatar_prompt,
            }
            for m in members
        ]

        return {
            "discussion_id": discussion_id,
            "panel_confirmed": True,
            "members": members_response,
        }
