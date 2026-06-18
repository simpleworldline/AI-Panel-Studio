"""Abstract Agent Base — Agent-Mediator 模式中的 Agent 基类"""

import abc
import uuid
from typing import AsyncGenerator


class BaseAgent(abc.ABC):
    """所有 Agent（主持人/专家/观察员）的抽象基类"""

    def __init__(self, member_id: str, name: str, title: str, stance: str, color: str):
        self.member_id = member_id
        self.name = name
        self.title = title
        self.stance = stance
        self.color = color
        self._focus: str | None = None
        self._desire: float = 0.0
        self._rounds_silent: int = 0

    @property
    def focus_summary(self) -> str | None:
        return self._focus

    @property
    def desire_value(self) -> float:
        return self._desire

    @property
    def rounds_silent(self) -> int:
        return self._rounds_silent

    def mark_silent(self):
        self._rounds_silent += 1

    def mark_spoke(self):
        self._rounds_silent = 0

    async def prepare(self, transcript: list[dict], topic: str):
        """计算欲望值 + 更新关注点摘要（子类可覆盖）"""
        self._desire = await self.calculate_desire(transcript, topic)

    @abc.abstractmethod
    async def calculate_desire(self, transcript: list[dict], topic: str) -> float:
        """计算发言欲望值 0.0-1.0"""
        ...

    @abc.abstractmethod
    async def generate_utterance(self, transcript: list[dict], topic: str) -> AsyncGenerator[str, None]:
        """流式生成发言（逐 token yield）"""
        ...
