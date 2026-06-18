"""Host Agent — 主持人，对齐 BACKEND_STRUCTURE.md §2.3 + §3.2

特点:
- 参与欲望值竞争 (与专家相同的四维度)
- 开场/总结阶段 desire=1.0 (流程节点)
- 四种发言: opening / question / follow_up / summary
"""

import time
import re


class HostAgent:
    W_TOPIC = 0.35
    W_RESPONSE = 0.30
    W_SILENCE = 0.20
    W_NOVELTY = 0.15

    def __init__(self, member_id, name, title, stance, color, llm_client):
        self.member_id = member_id
        self.name = name
        self.title = title
        self.stance = stance
        self.color = color
        self.role = "host"
        self._llm = llm_client
        self.desire = 0.0
        self.focus_time = time.time()

    def calculate_desire(
        self, transcript, current_focus, rounds_since_last_spoke=0, phase="discussion"
    ) -> float:
        """主持人的欲望值计算 — 流程节点直接拉满"""
        if phase in ("opening", "closing"):
            self.desire = 1.0
            self.focus_time = time.time()
            return 1.0
        # 讨论阶段: 与专家相同维度
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

    def _topic_relevance(self, focus):
        if not focus:
            return 0.3
        kw = re.findall(r"[一-鿿]{2,}", self.stance)
        if not kw:
            return 0.5
        return min(sum(1 for k in kw if k in focus) / len(kw), 1.0)

    def _response_need(self, transcript):
        if not transcript:
            return 0.1
        last = transcript[-1].get("content", "")
        kw = re.findall(r"[一-鿿]{2,}", self.stance)
        if not kw:
            return 0.2
        return min(sum(1 for k in kw if k in last) / len(kw) + 0.2, 1.0)

    def _silence_compensation(self, rounds):
        if rounds <= 0:
            return 0.0
        return min(rounds / 5.0, 1.0)

    def _novelty_score(self):
        return 0.5

    # ── 发言生成 ──

    async def generate_utterance(self, transcript, current_focus, utterance_type):
        prompt = self._build_prompt(transcript, current_focus, utterance_type)
        async for token in self._llm.chat_stream([{"role": "user", "content": prompt}]):
            yield token

    def generate_utterance_sync(self, transcript, current_focus, utterance_type):
        import asyncio
        prompt = self._build_prompt(transcript, current_focus, utterance_type)
        return asyncio.run(self._llm.chat([{"role": "user", "content": prompt}]))

    def _build_prompt(self, transcript, current_focus, utterance_type):
        history = "\n".join(
            f"{u['member_name']}: {u['content']}" for u in transcript[-20:]  # 更多上下文
        )
        type_guide = {
            "opening": "请作为主持人做开场介绍，简短介绍话题和各位嘉宾。",
            "question": "请作为主持人向某位嘉宾提出一个引导性问题。",
            "follow_up": "请作为主持人对当前内容进行追问，推动讨论深入。",
            "summary": (
                "请作为主持人用自然语言总结今天的讨论。总结必须包含: "
                "1. 讨论的核心议题 2. 各方主要观点 3. 达成的共识 4. 存在的分歧。"
                "用连贯的段落输出，不要使用JSON格式或编号列表。"
            ),
        }
        return (
            f"你是一位圆桌讨论的主持人。\n"
            f"你的名字: {self.name}\n"
            f"你的头衔: {self.title}\n"
            f"你的立场: {self.stance}\n"
            f"当前阶段: {current_focus}\n\n"
            f"完整讨论记录:\n{history}\n\n"
            f"{type_guide.get(utterance_type, '请发表你的主持发言。')}\n"
            f"要求: 用中文，只输出发言内容，不输出JSON。"
        )

    def get_focus_summary(self, transcript, current_focus):
        if not transcript:
            return f"准备开场介绍话题: {current_focus}"
        return f"正在引导讨论: {current_focus}"
