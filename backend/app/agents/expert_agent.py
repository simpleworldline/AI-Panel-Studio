"""Expert Agent — 专家嘉宾"""

import random
from typing import AsyncGenerator

from app.agents.base_agent import BaseAgent
from app.agents.llm_client import llm_client

EXPERT_SYSTEM_PROMPT = """你是一位圆桌讨论的嘉宾专家。你的立场、背景由系统指定。
发言要求：
1. 紧紧围绕主题和自身立场表达观点
2. 每次1-2句话，使用中文
3. 可以回应/反驳其他嘉宾的观点
4. 表达自然流畅，不使用JSON或格式化字符
5. 不暴露你的内部思考过程或"作为AI"这类表述
6. 保持专业但不失生动

记住：你是节目中一位真实的专家嘉宾，不是AI助手。"""


class ExpertAgent(BaseAgent):
    """专家 Agent — 自主发言 + 欲望值竞争"""

    def __init__(self, member_id: str, name: str, title: str, stance: str, color: str):
        super().__init__(member_id, name, title, stance, color)

    async def calculate_desire(self, transcript: list[dict], topic: str) -> float:
        """欲望值计算：话题相关度 0.35 + 回应需求度 0.30 + 沉默补偿 0.20 + 观点新鲜度 0.15

        当前使用简化版计算（LLM计算成本高）:
        - 随机基础值 0.2-0.6
        - 每次沉默 +0.1
        - 若上一发言提及相关关键词 +0.15
        """
        base = random.uniform(0.2, 0.6)
        silence_bonus = min(self._rounds_silent * 0.12, 0.3)

        # 检查最近发言是否与自身立场相关
        relevance_bonus = 0.0
        if transcript:
            last = transcript[-1]
            content = last.get("content", "")
            # 简单关键词匹配
            stance_keywords = [w for w in self.stance[:20] + self.title[:10] if len(w) >= 1]
            if any(kw in content for kw in stance_keywords):
                relevance_bonus = 0.15

        desire = min(base + silence_bonus + relevance_bonus, 1.0)
        self._focus = f"关注中... (欲望值: {desire:.2f})"
        return desire

    async def generate_utterance(self, transcript: list[dict], topic: str) -> AsyncGenerator[str, None]:
        """生成专家发言"""
        context = _build_context(transcript, self.name, self.title, self.stance, topic)
        messages = llm_client.create_messages(EXPERT_SYSTEM_PROMPT, context)
        async for token in llm_client.chat_stream(messages, max_tokens=200):
            yield token


def _build_context(transcript: list[dict], name: str, title: str, stance: str, topic: str) -> str:
    lines = [
        f"讨论主题：「{topic}」",
        f"你的身份：{name}，{title}",
        f"你的立场：{stance}",
    ]
    if transcript:
        lines.append("已有发言记录：")
        for u in transcript[-8:]:
            n = u.get("member_name", u.get("memberName", "Unknown"))
            c = u.get("content", "")
            lines.append(f"  [{n}]: {c}")
    else:
        lines.append("讨论即将开始，请准备。")
    lines.append("请发表你的观点，1-2句话。")
    return "\n".join(lines)
