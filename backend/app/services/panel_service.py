"""嘉宾服务 — LLM 生成 + 编辑确认"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.discussion import Discussion
from app.models.panel_member import PanelMember
from app.schemas.panel import PanelConfirmRequest
from app.services.discussion_service import StatusError


class PanelService:

    def __init__(self, session: AsyncSession, llm_client, creator_session_id: str):
        self._session = session
        self._llm = llm_client
        self._creator = creator_session_id

    async def generate(self, discussion_id: str, regenerate_member_id: str | None = None):
        d = await self._get_discussion(discussion_id)
        self._assert_creator(d)
        self._assert_not_confirmed(d)

        import asyncio
        prompt = self._build_generate_prompt(d.topic, d.expert_count)
        try:
            result = await self._llm.chat_json([{"role": "user", "content": prompt}])
        except Exception:
            # fallback — 生成默认阵容
            result = self._fallback_panel(d.topic, d.expert_count)

        host_data = result.get("host", {})
        experts_data = result.get("experts", [])

        return {
            "host": {
                "name": host_data.get("name", "张明"),
                "title": host_data.get("title", "AI伦理学家"),
                "role": "host",
                "stance": host_data.get("stance", "中立客观"),
                "color": host_data.get("color", "#6366F1"),
            },
            "experts": [
                {
                    "name": e.get("name", f"专家{i+1}"),
                    "title": e.get("title", "研究员"),
                    "role": "expert",
                    "stance": e.get("stance", "观点待定"),
                    "color": e.get("color", self._default_colors[i % len(self._default_colors)]),
                }
                for i, e in enumerate(experts_data[:d.expert_count])
            ],
        }

    async def confirm(self, discussion_id: str, data: PanelConfirmRequest):
        d = await self._get_discussion(discussion_id)
        self._assert_creator(d)
        self._assert_not_confirmed(d)

        # 删除旧 panel (如有)
        old = (await self._session.execute(
            select(PanelMember).where(PanelMember.discussion_id == discussion_id)
        )).scalars().all()
        for m in old:
            await self._session.delete(m)

        # 写入主持人
        host = PanelMember(
            id=str(uuid.uuid4()),
            discussion_id=discussion_id,
            name=data.host.name,
            title=data.host.title,
            role="host",
            stance=data.host.stance,
            color=data.host.color,
            sort_order=0,
        )
        self._session.add(host)

        # 写入专家
        members = [host]
        for i, exp in enumerate(data.experts):
            pm = PanelMember(
                id=str(uuid.uuid4()),
                discussion_id=discussion_id,
                name=exp.name,
                title=exp.title,
                role="expert",
                stance=exp.stance,
                color=exp.color,
                sort_order=i + 1,
            )
            self._session.add(pm)
            members.append(pm)

        await self._session.commit()
        return [self._dict(m) for m in members]

    # ── helpers ──

    def _build_generate_prompt(self, topic: str, expert_count: int) -> str:
        return (
            f'请为话题「{topic}」设计一个圆桌讨论的嘉宾阵容。\n'
            f'包含 1 位主持人 + {expert_count} 位专家。\n'
            f'每位嘉宾需包含: name(中文姓名)、title(职业/头衔)、stance(对话题的立场)、color(HEX颜色码)。\n'
            f'以 JSON 格式输出:\n'
            f'{{"host": {{"name":"...","title":"...","stance":"...","color":"#6366F1"}}, '
            f'"experts": [{{"name":"...","title":"...","stance":"...","color":"#..."}}] }}'
        )

    def _fallback_panel(self, topic: str, count: int) -> dict:
        names = [("李研究员", "认知科学高级研究员", "支持"), ("王博士", "计算机科学教授", "谨慎"),
                  ("陈女士", "科技伦理委员会主席", "反对"), ("赵工程师", "AI系统架构师", "中立"),
                  ("刘教授", "认知神经科学家", "支持"), ("孙博士", "法律与AI研究员", "反对"),
                  ("周科学家", "深度学习研究员", "支持"), ("吴伦理师", "应用伦理学教授", "反对")]
        return {
            "host": {"name": "张明", "title": "AI伦理学家", "stance": "中立客观，引导讨论", "color": "#6366F1"},
            "experts": [
                {"name": n, "title": t, "stance": s, "color": self._default_colors[i % 8]}
                for i, (n, t, s) in enumerate(names[:count])
            ],
        }

    _default_colors = ["#EF4444", "#3B82F6", "#F59E0B", "#10B981", "#8B5CF6", "#EC4899", "#06B6D4", "#F97316"]

    async def _get_discussion(self, discussion_id):
        d = await self._session.get(Discussion, discussion_id)
        if not d:
            raise StatusError(40401, "讨论不存在")
        return d

    def _assert_creator(self, d: Discussion):
        if d.creator_session_id != self._creator:
            raise StatusError(40301, "非创建者无权操作")

    def _assert_not_confirmed(self, d: Discussion):
        pass  # 允许重复确认 (覆盖)

    @staticmethod
    def _dict(obj):
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
