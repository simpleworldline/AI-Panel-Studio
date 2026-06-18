"""Agent 抽象基类 — 定义 Agent 最小接口"""

from typing import Protocol, AsyncGenerator


class AgentProtocol(Protocol):
    """Scheduler 需要的 Agent 接口"""
    member_id: str
    role: str
    desire: float
    focus_time: float
