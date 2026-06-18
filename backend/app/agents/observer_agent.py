"""Observer Agent — 独立观察员（共识/分歧提炼）"""

from app.agents.llm_client import llm_client

OBSERVER_SYSTEM_PROMPT = """你是一位圆桌讨论的独立观察员。你的职责是增量分析每条新发言，判断是否产生新的共识或分歧。

输出格式要求：严格输出 JSON (仅此一次)：
{
  "action": "created|updated|resolved",
  "type": "consensus|disagreement",
  "title": "简短标题 ≤30字",
  "description": "详细说明 ≤200字",
  "source_utterance_ids": ["u-1", "u-5"],
  "confidence": 0.85,
  "is_resolved": false,
  "round_num": N
}

如果本发言没有产生新的共识或分歧，输出：{"action": "none"}
不要输出其他内容。"""


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
