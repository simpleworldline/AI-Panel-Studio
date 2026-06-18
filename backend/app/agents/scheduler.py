"""发言欲望值调度仲裁器 — 严格遵循 BACKEND_STRUCTURE.md §3.2

决断链: desire_value ↓ → focus_time ↑ (关注点越新越优先) → random
主持人同分时优先于专家。
"""

import random
from typing import Protocol


class AgentLike(Protocol):
    """Scheduler 依赖的最小 Agent 接口"""
    member_id: str
    role: str       # "host" | "expert"
    desire: float   # 0.00 - 1.00
    focus_time: float  # epoch seconds


class Scheduler:
    """欲望值调度仲裁器"""

    def select_speaker(self, agents: list[AgentLike]) -> AgentLike:
        """从 agent 列表中选出本轮发言者。

        Raises:
            ValueError: agents 为空
        """
        if not agents:
            raise ValueError("至少需要一个 agent 才能调度发言")

        # 1. 找最高 desire 值
        max_desire = max(a.desire for a in agents)
        candidates = [a for a in agents if a.desire == max_desire]

        if len(candidates) == 1:
            return candidates[0]

        # 2. 主持人优先 (在同 desire 组内)
        hosts = [a for a in candidates if a.role == "host"]
        if hosts:
            candidates = hosts

        if len(candidates) == 1:
            return candidates[0]

        # 3. 关注点时间距离 (focus_time 越大越近)
        max_focus = max(a.focus_time for a in candidates)
        candidates = [a for a in candidates if a.focus_time == max_focus]

        if len(candidates) == 1:
            return candidates[0]

        # 4. 随机
        idx = self._random_index(len(candidates))
        return candidates[idx]

    def _random_index(self, n: int) -> int:
        """返回 0..n-1 的随机整数 (可被 monkeypatch)"""
        return random.randint(0, n - 1)
