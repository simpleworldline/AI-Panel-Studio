"""Expert Agent — 严格遵循 BACKEND_STRUCTURE.md §3.2

欲望值四维度:
- 话题相关度 (0.35): 关键词匹配
- 回应需求度 (0.30): 最新发言是否提及本方领域
- 沉默补偿 (0.20): 连续未发言轮次
- 观点新鲜度 (0.15): 是否有未表达观点
"""

import time
import re


class ExpertAgent:
    """专家 Agent — 自主发言，欲望值竞争"""

    # 维度权重
    W_TOPIC = 0.35
    W_RESPONSE = 0.30
    W_SILENCE = 0.20
    W_NOVELTY = 0.15

    def __init__(
        self,
        member_id: str,
        name: str,
        title: str,
        stance: str,
        color: str,
        llm_client,
    ):
        self.member_id = member_id
        self.name = name
        self.title = title
        self.stance = stance
        self.color = color
        self.role = "expert"
        self._llm = llm_client
        self.desire = 0.0
        self.focus_time = time.time()

    # ================================================================
    # 欲望值计算 (纯算法, 不调 LLM)
    # ================================================================

    def calculate_desire(
        self,
        transcript: list[dict],
        current_focus: str,
        rounds_since_last_spoke: int = 0,
    ) -> float:
        """计算发言欲望值 0.0-1.0"""
        topic_rel = self._topic_relevance(current_focus)
        response = self._response_need(transcript)
        silence = self._silence_compensation(rounds_since_last_spoke)
        novelty = self._novelty_score()

        total = (
            self.W_TOPIC * topic_rel
            + self.W_RESPONSE * response
            + self.W_SILENCE * silence
            + self.W_NOVELTY * novelty
        )
        self.desire = min(max(total, 0.0), 1.0)
        self.focus_time = time.time()
        return self.desire

    def _topic_relevance(self, focus: str) -> float:
        """立场关键词与当前焦点匹配度"""
        if not focus:
            return 0.3
        keywords = self._extract_keywords(self.stance)
        if not keywords:
            return 0.5
        matched = sum(1 for kw in keywords if kw in focus)
        return min(matched / max(len(keywords), 1), 1.0)

    def _response_need(self, transcript: list[dict]) -> float:
        """最新发言是否涉及本方立场"""
        if not transcript:
            return 0.1
        last = transcript[-1].get("content", "")
        keywords = self._extract_keywords(self.stance)
        if not keywords:
            return 0.2
        matched = sum(1 for kw in keywords if kw in last)
        return min(matched / max(len(keywords), 1) + 0.2, 1.0)

    def _silence_compensation(self, rounds: int) -> float:
        """沉默越久，欲望越高 (5 轮后饱和)"""
        if rounds <= 0:
            return 0.0
        return min(rounds / 5.0, 1.0)

    def _novelty_score(self) -> float:
        """是否有未表达的观点 (简化: 常量中等值, 由 LLM 在 generate 时体现)"""
        return 0.5

    @staticmethod
    def _extract_keywords(text: str) -> list[str]:
        """从立场文本中提取关键词"""
        # 取 2 字以上的中文词
        words = re.findall(r"[一-鿿]{2,}", text)
        return list(set(words))

    # ================================================================
    # 发言生成 (调 LLM)
    # ================================================================

    async def generate_utterance(self, transcript: list[dict], current_focus: str, **kwargs):
        """异步流式生成发言 (生产用)"""
        prompt = self._build_prompt(transcript, current_focus)
        messages = [{"role": "user", "content": prompt}]
        async for token in self._llm.chat_stream(messages):
            yield token

    def generate_utterance_sync(self, transcript: list[dict], current_focus: str) -> str:
        """同步生成发言 (测试用 — 使用 MockLLMClient.chat)"""
        prompt = self._build_prompt(transcript, current_focus)
        messages = [{"role": "user", "content": prompt}]
        import asyncio
        return asyncio.run(self._llm.chat(messages))

    def _build_prompt(self, transcript: list[dict], current_focus: str) -> str:
        """构建发言 prompt — 禁止暴露 CoT"""
        history = "\n".join(
            f"{u['member_name']}: {u['content']}" for u in transcript[-6:]
        )
        return (
            f"你是一位专家嘉宾，参加一场AI圆桌讨论。\n"
            f"你的名字: {self.name}\n"
            f"你的头衔: {self.title}\n"
            f"你的立场: {self.stance}\n"
            f"当前讨论焦点: {current_focus}\n\n"
            f"最近发言记录:\n{history}\n\n"
            f"请发表你的观点(1-2句话)，可以补充、反驳、或提出新观点。\n"
            f"要求: 用中文发言，只输出发言内容，不要输出思考过程或JSON。"
        )

    # ================================================================
    # 关注点摘要 (纯算法)
    # ================================================================

    def get_focus_summary(self, transcript: list[dict], current_focus: str) -> str:
        """生成公开思考摘要 — 不含内部 CoT"""
        if not transcript:
            return f"正在思考关于{current_focus}的观点"
        last_speaker = transcript[-1].get("member_name", "上一位发言人")
        return f"正在思考{last_speaker}关于{current_focus}的观点，准备从{self.stance[:20]}角度回应"
