"""讨论服务 — 生命周期管理、列表查询、详情聚合"""

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.discussion import Discussion
from app.models.panel_member import PanelMember
from app.models.utterance import Utterance
from app.schemas.discussion import DiscussionCreate


class DiscussionService:

    def __init__(self, session: AsyncSession, creator_session_id: str):
        self._session = session
        self._creator = creator_session_id

    async def create(self, data: DiscussionCreate) -> Discussion:
        import uuid
        d = Discussion(
            id=str(uuid.uuid4()),
            topic=data.topic,
            expert_count=data.expert_count,
            max_rounds=data.max_rounds,
            creator_session_id=self._creator,
        )
        self._session.add(d)
        await self._session.commit()
        return d

    async def list_all(self, status: str | None = None, page: int = 1, page_size: int = 20):
        q = select(Discussion)
        if status:
            q = q.where(Discussion.status == status)
        q = q.order_by(Discussion.created_at.desc())

        # count
        count_q = select(func.count()).select_from(Discussion)
        if status:
            count_q = count_q.where(Discussion.status == status)
        total = (await self._session.execute(count_q)).scalar() or 0

        offset = (page - 1) * page_size
        q = q.offset(offset).limit(page_size)
        rows = (await self._session.execute(q)).scalars().all()

        items = []
        for d in rows:
            members = await self._get_member_previews(d.id)
            items.append({
                "id": d.id,
                "topic": d.topic,
                "expert_count": d.expert_count,
                "status": d.status,
                "current_round": d.current_round,
                "created_at": d.created_at,
                "member_preview": members,
            })
        return items, total

    async def get_detail(self, discussion_id: str):
        d = await self._get_discussion(discussion_id)
        panel = await self._get_panel(discussion_id)
        transcript = await self._get_transcript(discussion_id)
        consensus, disagreements = await self._get_consensus(discussion_id)
        return {
            **self._dict(d),
            "panel": panel,
            "transcript": transcript,
            "consensus": consensus,
            "disagreements": disagreements,
        }

    async def start(self, discussion_id: str):
        d = await self._get_discussion(discussion_id)
        self._assert_creator(d)
        self._assert_status(d, "pending")
        d.status = "live"
        await self._session.commit()
        return d

    async def pause(self, discussion_id: str):
        d = await self._get_discussion(discussion_id)
        self._assert_creator(d)
        if d.status != "live":
            raise StatusError(40902, "讨论不在直播状态")
        d.status = "paused"
        await self._session.commit()
        return d

    async def resume(self, discussion_id: str):
        d = await self._get_discussion(discussion_id)
        self._assert_creator(d)
        if d.status != "paused":
            raise StatusError(40902, "讨论不在暂停状态")
        d.status = "live"
        await self._session.commit()
        return d

    async def end(self, discussion_id: str):
        d = await self._get_discussion(discussion_id)
        self._assert_creator(d)
        if d.status == "ended":
            raise StatusError(40901, "讨论已结束不可操作")
        d.status = "ended"
        d.ended_at = datetime.now(timezone.utc).isoformat()
        await self._session.commit()
        return d

    # ── helpers ──

    async def _get_discussion(self, discussion_id: str) -> Discussion:
        d = await self._session.get(Discussion, discussion_id)
        if not d:
            raise StatusError(40401, "讨论不存在")
        return d

    async def _get_member_previews(self, discussion_id: str):
        q = select(PanelMember).where(PanelMember.discussion_id == discussion_id).order_by(PanelMember.sort_order)
        rows = (await self._session.execute(q)).scalars().all()
        return [{"name": r.name, "role": r.role, "color": r.color} for r in rows]

    async def _get_panel(self, discussion_id: str):
        q = select(PanelMember).where(PanelMember.discussion_id == discussion_id).order_by(PanelMember.sort_order)
        rows = (await self._session.execute(q)).scalars().all()
        return [self._dict(r) for r in rows]

    async def _get_transcript(self, discussion_id: str):
        q = select(Utterance).where(Utterance.discussion_id == discussion_id).order_by(Utterance.sequence_num)
        rows = (await self._session.execute(q)).scalars().all()
        result = []
        for r in rows:
            member = await self._session.get(PanelMember, r.panel_member_id)
            result.append({
                "id": r.id,
                "panel_member_id": r.panel_member_id,
                "member_name": member.name if member else "未知",
                "member_title": member.title if member else "",
                "member_color": member.color if member else "#FFFFFF",
                "content": r.content,
                "utterance_type": r.utterance_type,
                "sequence_num": r.sequence_num,
                "round_num": r.round_num,
                "is_streaming": bool(r.is_streaming),
                "created_at": r.created_at,
            })
        return result

    async def _get_consensus(self, discussion_id: str):
        from app.models.consensus import ConsensusDisagreement
        q = select(ConsensusDisagreement).where(ConsensusDisagreement.discussion_id == discussion_id)
        rows = (await self._session.execute(q)).scalars().all()
        consensus_list = [self._dict(r) for r in rows if r.type == "consensus"]
        dis_list = [self._dict(r) for r in rows if r.type == "disagreement"]
        return consensus_list, dis_list

    def _assert_creator(self, d: Discussion):
        if d.creator_session_id != self._creator:
            raise StatusError(40301, "非创建者无权操作")

    def _assert_status(self, d: Discussion, expected: str):
        if d.status != expected:
            raise StatusError(40902, f"讨论状态不允许此操作 (当前: {d.status})")

    @staticmethod
    def _dict(obj):
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


class StatusError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)
