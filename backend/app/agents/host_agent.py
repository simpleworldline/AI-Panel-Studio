"""Host Agent — 主持人"""

from typing import AsyncGenerator

from app.agents.base_agent import BaseAgent
from app.agents.llm_client import llm_client

HOST_SYSTEM_PROMPT = """你是一位专业的圆桌讨论主持人。你的职责是：
1. 以开场白介绍话题并欢迎嘉宾
2. 在讨论中适时提问或引导话题转换
3. 对关键观点进行追问以深化讨论
4. 在讨论结束时进行总结，提炼核心观点、共识与分歧

发言要求：每次1-3句话，使用中文，表达自然流畅。
保持中立客观，不使用JSON或格式化字符。不做机械轮替。"""

SUMMARY_SYSTEM_PROMPT = """你是一位专业主持人，现在需要为讨论做最终总结。
请用自然语言总结：
1. 核心观点和洞见
2. 达成的共识
3. 存在的分歧
字数：100-300字，使用中文，不使用JSON或格式化字符。"""


class HostAgent(BaseAgent):
    """主持人 Agent — 开场/提问/追问/总结"""

    def __init__(self, member_id: str, name: str, title: str, stance: str, color: str):
        super().__init__(member_id, name, title, stance, color)

    async def calculate_desire(self, transcript: list[dict], topic: str) -> float:
        """主持人欲望值计算：
        - 开场（transcript 为空）→ 1.0
        - 讨论中 → 0.3~0.6 (需要时介入)
        - 同分优先于专家
        """
        if not transcript:
            return 1.0
        # 流程权重: 每隔几轮主持人可以介入
        base = 0.3
        if self._rounds_silent >= 3:
            base += 0.3
        return min(base, 0.6)

    async def generate_utterance(self, transcript: list[dict], topic: str) -> AsyncGenerator[str, None]:
        """生成主持人发言"""
        if not transcript:
            # 开场白
            prompt = f"讨论主题：「{topic}」。请做开场白，简短介绍话题，欢迎所有嘉宾。"
            messages = llm_client.create_messages(HOST_SYSTEM_PROMPT, prompt)
        else:
            # 提问/串场
            recent = _format_transcript(transcript, last_n=5)
            prompt = f"主题：「{topic}」\n最近发言:\n{recent}\n请适时提问或引导话题转换，1-2句话。"
            messages = llm_client.create_messages(HOST_SYSTEM_PROMPT, prompt)

        async for token in llm_client.chat_stream(messages, max_tokens=300):
            yield token

    async def generate_summary(self, transcript: list[dict], topic: str) -> AsyncGenerator[str, None]:
        """生成主持人总结"""
        full_text = _format_transcript(transcript, last_n=0)
        prompt = f"主题：「{topic}」\n完整讨论记录:\n{full_text}\n请做最终总结。"
        messages = llm_client.create_messages(SUMMARY_SYSTEM_PROMPT, prompt)
        async for token in llm_client.chat_stream(messages, max_tokens=500):
            yield token


def _format_transcript(transcript: list[dict], last_n: int = 5) -> str:
    """将 transcript 格式化为文本"""
    items = transcript[-last_n:] if last_n > 0 else transcript
    lines = []
    for u in items:
        name = u.get("member_name", u.get("memberName", "Unknown"))
        content = u.get("content", "")
        lines.append(f"[{name}]: {content}")
    return "\n".join(lines)
