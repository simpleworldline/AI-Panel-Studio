"""DiscussionService — 讨论生命周期管理"""

import uuid
from typing import AsyncGenerator

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.discussion import Discussion
from app.models.panel_member import PanelMember
from app.models.utterance import Utterance
from app.models.utterance import Utterance
from app.models.consensus import ConsensusDisagreement


class PermissionError(Exception):
    pass


class StateConflictError(Exception):
    pass


class DiscussionService:

    @staticmethod
    async def create(
        session: AsyncSession,
        topic: str,
        creator_session_id: str,
        expert_count: int = 4,
        max_rounds: int | None = None,
    ) -> Discussion:
        d = Discussion(
            id=str(uuid.uuid4()),
            topic=topic,
            expert_count=expert_count,
            max_rounds=max_rounds,
            creator_session_id=creator_session_id,
        )
        session.add(d)
        await session.flush()
        await session.refresh(d)
        return d

    @staticmethod
    async def list_discussions(
        session: AsyncSession,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        stmt = select(Discussion)
        count_stmt = select(func.count(Discussion.id))

        if status:
            stmt = stmt.where(Discussion.status == status)
            count_stmt = count_stmt.where(Discussion.status == status)

        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = stmt.order_by(Discussion.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await session.execute(stmt)
        discussions = result.scalars().all()

        # Build items with member_preview
        items = []
        for d in discussions:
            member_result = await session.execute(
                select(PanelMember).where(PanelMember.discussion_id == d.id).order_by(PanelMember.sort_order).limit(2)
            )
            members = member_result.scalars().all()
            items.append({
                "id": d.id,
                "topic": d.topic,
                "expert_count": d.expert_count,
                "status": d.status,
                "current_round": d.current_round,
                "created_at": d.created_at,
                "member_preview": [{"name": m.name, "role": m.role} for m in members],
            })

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    @staticmethod
    async def get_detail(session: AsyncSession, discussion_id: str) -> dict | None:
        stmt = select(Discussion).where(Discussion.id == discussion_id).options(
            selectinload(Discussion.panel_members),
            selectinload(Discussion.utterances).selectinload(Utterance.panel_member),
            selectinload(Discussion.consensus_disagreements),
        )
        result = await session.execute(stmt)
        d = result.scalar_one_or_none()
        if d is None:
            return None

        panel = [
            {
                "id": m.id, "name": m.name, "title": m.title, "role": m.role,
                "stance": m.stance, "color": m.color,
            }
            for m in d.panel_members
        ]
        transcript = [
            {
                "id": u.id, "panel_member_id": u.panel_member_id, "member_name": u.panel_member.name,
                "member_title": u.panel_member.title, "member_color": u.panel_member.color,
                "content": u.content, "utterance_type": u.utterance_type,
                "sequence_num": u.sequence_num, "round_num": u.round_num,
                "created_at": u.created_at,
            }
            for u in d.utterances
        ]
        consensus_items = [
            {
                "id": c.id, "type": c.type, "title": c.title, "description": c.description,
                "source_utterance_ids": c.source_utterance_ids, "confidence": c.confidence,
                "is_resolved": bool(c.is_resolved), "round_num": c.round_num,
            }
            for c in d.consensus_disagreements if c.type == "consensus"
        ]
        disagreements = [
            {
                "id": c.id, "type": c.type, "title": c.title, "description": c.description,
                "source_utterance_ids": c.source_utterance_ids, "confidence": c.confidence,
                "is_resolved": bool(c.is_resolved), "round_num": c.round_num,
            }
            for c in d.consensus_disagreements if c.type == "disagreement"
        ]

        return {
            "id": d.id, "topic": d.topic, "expert_count": d.expert_count,
            "status": d.status, "current_round": d.current_round,
            "max_rounds": d.max_rounds, "created_at": d.created_at,
            "ended_at": d.ended_at, "creator_session_id": d.creator_session_id,
            "panel": panel, "transcript": transcript,
            "consensus": consensus_items, "disagreements": disagreements,
        }

    @staticmethod
    async def check_permission(session: AsyncSession, discussion_id: str, session_id: str) -> Discussion:
        """验证创建者权限，返回 Discussion"""
        d = await session.get(Discussion, discussion_id)
        if d is None:
            raise PermissionError("讨论不存在")
        if d.creator_session_id != session_id:
            raise PermissionError("非创建者无权操作")
        return d

    @staticmethod
    async def check_panel_confirmed(session: AsyncSession, discussion_id: str) -> bool:
        """检查阵容是否已确认"""
        result = await session.execute(
            select(func.count(PanelMember.id)).where(PanelMember.discussion_id == discussion_id)
        )
        count = result.scalar() or 0
        result2 = await session.execute(
            select(func.count(PanelMember.id)).where(
                PanelMember.discussion_id == discussion_id, PanelMember.role == "host"
            )
        )
        host_count = result2.scalar() or 0
        return count > 0 and host_count > 0

    @staticmethod
    async def start(session: AsyncSession, discussion_id: str) -> dict:
        d = await session.get(Discussion, discussion_id)
        if d is None:
            raise PermissionError("讨论不存在")
        if d.status == "ended":
            raise StateConflictError("讨论已结束")
        if d.status == "live":
            return {"discussion_id": d.id, "status": d.status}

        # 检查阵容已确认
        has_host = await session.execute(
            select(func.count(PanelMember.id)).where(
                PanelMember.discussion_id == discussion_id, PanelMember.role == "host"
            )
        )
        if (has_host.scalar() or 0) == 0:
            raise StateConflictError("阵容未确认，无法开始讨论")

        d.status = "live"
        await session.flush()
        return {"discussion_id": d.id, "status": d.status}

    @staticmethod
    async def pause(session: AsyncSession, discussion_id: str) -> dict:
        d = await session.get(Discussion, discussion_id)
        if d is None:
            raise PermissionError("讨论不存在")
        if d.status != "live":
            raise StateConflictError("讨论不在直播状态")
        d.status = "paused"
        await session.flush()
        return {"discussion_id": d.id, "status": d.status}

    @staticmethod
    async def resume(session: AsyncSession, discussion_id: str) -> dict:
        d = await session.get(Discussion, discussion_id)
        if d is None:
            raise PermissionError("讨论不存在")
        if d.status != "paused":
            raise StateConflictError("讨论不在暂停状态")
        d.status = "live"
        await session.flush()
        return {"discussion_id": d.id, "status": d.status}

    @staticmethod
    async def next_round(session: AsyncSession, discussion_id: str) -> dict:
        d = await session.get(Discussion, discussion_id)
        if d is None:
            raise PermissionError("讨论不存在")
        if d.status != "live":
            raise StateConflictError("讨论不在直播状态")
        return {"discussion_id": d.id, "round_triggered": True}

    @staticmethod
    async def end(session: AsyncSession, discussion_id: str) -> dict:
        from datetime import datetime, timezone

        d = await session.get(Discussion, discussion_id)
        if d is None:
            raise PermissionError("讨论不存在")
        if d.status == "ended":
            raise StateConflictError("讨论已结束")

        # Count utterances
        result = await session.execute(
            select(func.count(Utterance.id)).where(Utterance.discussion_id == discussion_id)
        )
        total_utterances = result.scalar() or 0

        d.status = "ended"
        d.ended_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        await session.flush()
        return {
            "discussion_id": d.id, "status": d.status,
            "ended_at": d.ended_at, "total_rounds": d.current_round,
            "total_utterances": total_utterances,
        }
