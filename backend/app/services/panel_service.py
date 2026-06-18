"""PanelService — LLM-powered guest generation + edit/confirm"""

import json
import re
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discussion import Discussion
from app.models.panel_member import PanelMember
from app.schemas.panel import PanelConfirmRequest
from app.agents.llm_client import llm_client

EXPERT_COLORS = ["#6366F1", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#06B6D4", "#F97316"]

PANEL_SYSTEM_PROMPT = """你是一位专业的圆桌讨论策划人。根据用户给定的话题和专家人数，生成完整的嘉宾阵容。

要求:
1. 全部输出必须使用中文
2. 生成1位主持人（中立客观，善于引导讨论）
3. 生成N位专家（N等于用户指定的数量），每位专家立场各异，覆盖不同学科视角
4. 姓名使用2-3字中文姓名
5. title使用8-16字中文职业描述
6. stance使用10-30字中文立场描述

严格输出JSON（不要输出其他内容）：
{
  "host": {"name":"...", "title":"...", "stance":"..."},
  "experts": [{"name":"...", "title":"...", "stance":"..."}, ...]
}"""


class PanelService:

    @staticmethod
    async def generate_panel(
        session: AsyncSession,
        discussion_id: str,
        regenerate_member_id: str | None = None,
    ) -> dict:
        """LLM generate panel lineup, fallback to mock on failure"""
        d = await session.get(Discussion, discussion_id)
        if d is None:
            raise ValueError("discussion not found")

        # Call LLM for generation
        result = await _call_llm_generate(d.topic, d.expert_count)

        # Assign colors
        result["host"]["color"] = EXPERT_COLORS[0]
        result["host"]["avatar_prompt"] = None
        for i, expert in enumerate(result.get("experts", [])):
            expert["color"] = EXPERT_COLORS[(i + 1) % len(EXPERT_COLORS)]
            expert["avatar_prompt"] = None

        # Pad with mock if LLM returned fewer experts
        current_count = len(result.get("experts", []))
        if current_count < d.expert_count:
            for j in range(d.expert_count - current_count):
                idx = current_count + j
                result["experts"].append({
                    "name": _mock_experts[idx % len(_mock_experts)]["name"],
                    "title": _mock_experts[idx % len(_mock_experts)]["title"],
                    "stance": _mock_experts[idx % len(_mock_experts)]["stance"],
                    "color": EXPERT_COLORS[(idx + 1) % len(EXPERT_COLORS)],
                    "avatar_prompt": None,
                })

        # Truncate if too many
        result["experts"] = result["experts"][:d.expert_count]

        return result

    @staticmethod
    async def confirm_panel(
        session: AsyncSession,
        discussion_id: str,
        host: dict,
        experts: list[dict],
    ) -> dict:
        """Confirm and save panel lineup"""
        d = await session.get(Discussion, discussion_id)
        if d is None:
            raise ValueError("discussion not found")

        # Check if already confirmed
        existing_host = await session.execute(
            select(PanelMember).where(
                PanelMember.discussion_id == discussion_id, PanelMember.role == "host"
            )
        )
        if existing_host.scalar_one_or_none() is not None:
            raise ValueError("panel already confirmed, cannot modify")

        # Clear old members
        result = await session.execute(
            select(PanelMember).where(PanelMember.discussion_id == discussion_id)
        )
        for m in result.scalars().all():
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
                "role": m.role, "stance": m.stance, "color": m.color,
                "avatar_prompt": m.avatar_prompt,
            }
            for m in members
        ]

        return {
            "discussion_id": discussion_id,
            "panel_confirmed": True,
            "members": members_response,
        }


async def _call_llm_generate(topic: str, expert_count: int) -> dict:
    """Call LLM and parse JSON response. Falls back to mock on any error."""
    prompt = f"话题：「{topic}」\n需要的专家人数：{expert_count} 位"
    messages = llm_client.create_messages(PANEL_SYSTEM_PROMPT, prompt)

    try:
        raw = await llm_client.chat(messages, temperature=0.8, max_tokens=2048)
        if not raw:
            raise ValueError("LLM returned empty")

        # Strip markdown code fences if present
        cleaned = raw.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        parsed = json.loads(cleaned)
        if "host" not in parsed or "experts" not in parsed:
            raise ValueError("JSON missing host/experts")
        return parsed
    except Exception:
        return _fallback_panel(expert_count)


def _fallback_panel(expert_count: int) -> dict:
    """Fallback: return mock host + N experts"""
    return {
        "host": {
            "name": "张明",
            "title": "AI伦理学家",
            "stance": "中立客观，擅长引导讨论",
            "color": EXPERT_COLORS[0],
            "avatar_prompt": None,
        },
        "experts": [
            {
                **_mock_experts[i % len(_mock_experts)],
                "color": EXPERT_COLORS[(i + 1) % len(EXPERT_COLORS)],
                "avatar_prompt": None,
            }
            for i in range(expert_count)
        ],
    }


_mock_experts = [
    {"name": "李研究员", "title": "认知科学研究所高级研究员", "stance": "支持AI具备有限自我意识"},
    {"name": "王教授", "title": "计算机科学教授", "stance": "反对赋予AI自我意识，存在安全风险"},
    {"name": "陈博士", "title": "神经科学博士", "stance": "从生物学角度比较人类与AI意识"},
    {"name": "赵工程师", "title": "AI产品经理", "stance": "从产品实用角度讨论"},
    {"name": "孙教授", "title": "哲学系教授", "stance": "从伦理学视角审视AI意识问题"},
    {"name": "周博士", "title": "AI安全研究员", "stance": "关注AI自我意识带来的安全与监管"},
    {"name": "吴分析师", "title": "科技政策分析师", "stance": "从政策与法律角度评估AI意识的影响"},
    {"name": "郑主编", "title": "科技媒体主编", "stance": "从公众认知与科学传播角度参与讨论"},
]
