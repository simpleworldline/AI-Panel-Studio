"""Observer Agent — 独立观察员，对齐 BACKEND_STRUCTURE.md §3.3

职责: 对最新发言判断是否产生共识或分歧。
输出: 结构化字典 (action/type/title/description/confidence)，不进入Transcript。
"""

import json
import asyncio


class ObserverAgent:
    def __init__(self, member_id, name, llm_client):
        self.member_id = member_id
        self.name = name
        self.role = "observer"
        self._llm = llm_client

    async def analyze(
        self, transcript: list[dict], existing_consensus: list[dict], latest_utterance: dict
    ) -> dict:
        """异步分析 (生产用)"""
        prompt = self._build_prompt(transcript, existing_consensus, latest_utterance)
        return await self._llm.chat_json([{"role": "user", "content": prompt}])

    def analyze_sync(self, transcript, existing_consensus, latest_utterance) -> dict:
        """同步分析 (测试用)"""
        prompt = self._build_prompt(transcript, existing_consensus, latest_utterance)
        return asyncio.run(self._llm.chat_json([{"role": "user", "content": prompt}]))

    def _build_prompt(self, transcript, existing_consensus, latest_utterance) -> str:
        history = "\n".join(
            f"{u['member_name']}: {u['content']}" for u in transcript[-8:]
        )
        existing = json.dumps(existing_consensus, ensure_ascii=False, indent=2) if existing_consensus else "暂无"
        latest = json.dumps(latest_utterance, ensure_ascii=False)

        return (
            "你是一位圆桌讨论的独立观察员。你的任务是分析最新发言与先前发言之间是否产生共识或分歧。\n\n"
            f"已有共识/分歧:\n{existing}\n\n"
            f"完整讨论记录:\n{history}\n\n"
            f"最新发言:\n{latest}\n\n"
            "判断规则:\n"
            "1. 如果最新发言印证了已有观点 → action='updated', 更新已有共识/分歧\n"
            "2. 如果最新发言与已有观点冲突 → action='created', type='disagreement'\n"
            "3. 如果最新发言与已有观点一致 → action='created', type='consensus'\n"
            "4. 如果新发言未产生共识/分歧 → action='none'\n"
            "5. confidence 在 0.0-1.0 之间\n\n"
            "以 JSON 格式输出:\n"
            '{"action": "created|updated|resolved|none", "type": "consensus|disagreement", '
            '"title": "简短标题(≤20字)", "description": "详细说明(≤200字)", "confidence": 0.0-1.0}'
        )
