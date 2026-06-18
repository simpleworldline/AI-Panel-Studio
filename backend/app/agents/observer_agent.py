"""Observer Agent — 独立观察员（共识/分歧提炼）"""

from app.agents.llm_client import llm_client

OBSERVER_SYSTEM_PROMPT = """你是一位圆桌讨论的独立观察员。你的职责是增量分析每条新发言，判断是否产生新的共识或分歧。

输出格式要求：严格输出 JSON (不要输出其他任何内容)：
{
  "action": "created",
  "type": "consensus",
  "title": "识别出的共识或分歧的简短标题",
  "description": "综合发言内容，给出一条具体、有信息量的判断",
  "source_utterance_ids": ["u-1", "u-2"],
  "confidence": 0.85,
  "is_resolved": false,
  "round_num": 1
}

action 说明:
- created: 新产生了一个共识或分歧
- updated: 已有共识/分歧被新发言印证或增强
- resolved: 已有分歧被化解

type 说明:
- consensus: 两位及以上专家观点一致或相互支持
- disagreement: 两位及以上专家观点对立或冲突

判断标准:
- 仅当最新发言明确支持/反对/印证已有观点时才标记共识或分歧
- 置信度0-1, 0.7以上才输出, 低于则认为不够明确
- 如果最新发言只是陈述观点、没有与他人形成明确共识/分歧 → 输出 {"action": "none"}
- 不要做过度解读"""


class ObserverAgent:
    """独立观察员 — 实时共识/分歧分析"""

    async def analyze(
        self,
        transcript: list[dict],
        latest_utterance: dict,
        existing_consensus: list[dict],
    ) -> dict | None:
        """分析最新发言是否产生共识/分歧

        Returns: {"action": "created|updated|resolved", "record": {...}} 或 None
        """
        prompt = _build_observer_prompt(transcript, latest_utterance, existing_consensus)
        messages = llm_client.create_messages(OBSERVER_SYSTEM_PROMPT, prompt)

        raw = await llm_client.chat(messages, temperature=0.3, max_tokens=400)
        try:
            import json
            result = json.loads(raw.strip())
        except (json.JSONDecodeError, ValueError):
            return None

        if result.get("action") == "none":
            return None
        return result


def _build_observer_prompt(
    transcript: list[dict],
    latest: dict,
    existing: list[dict],
) -> str:
    lines = ["完整发言记录："]
    for u in transcript[-10:]:
        n = u.get("member_name", u.get("memberName", "Unknown"))
        c = u.get("content", "")
        uid = u.get("id", u.get("utteranceId", "?"))
        lines.append(f"  [{uid}] {n}: {c}")

    lines.append("")
    lines.append("最新发言：")
    lines.append(f"  [{latest.get('id', '?')}] {latest.get('member_name', latest.get('memberName', '?'))}: {latest.get('content', '')}")

    if existing:
        lines.append("")
        lines.append("已有共识/分歧：")
        for c in existing:
            lines.append(f"  [{c.get('type', '')}] {c.get('title', '')}: {c.get('description', '')}")

    lines.append("")
    lines.append("请判断最新发言是否产生新的共识或分歧。")
    return "\n".join(lines)
