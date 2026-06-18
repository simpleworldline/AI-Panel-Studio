"""Scheduler — 欲望值调度仲裁器"""

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agents.base_agent import BaseAgent


class Scheduler:
    """发言欲望值调度仲裁器

    决断链：desire_value ↓ → 关注点时间距离 → 随机
    主持人同分时优先于专家
    """

    @staticmethod
    async def select_speaker(agents: list["BaseAgent"]) -> "BaseAgent | None":
        """从 Agent 列表中选择发言者

        1. 按 desire_value 降序排序
        2. 同分时：主持人优先
        3. 仍同分：随机选择
        """
        if not agents:
            return None

        # 按 desire_value 降序，主持人同分优先
        def sort_key(agent: "BaseAgent") -> tuple:
            is_host = 1 if agent.__class__.__name__ == "HostAgent" else 0
            # 反向 desire_value（降序），host flag 正向（同分时 host 优先）
            return (-agent.desire_value, -is_host)

        # 如果有 Agent desire_value 低于阈值则不发言
        active = [a for a in agents if a.desire_value >= 0.3]
        if not active:
            return None

        active.sort(key=sort_key)

        # 取最高 desire 的群体，同分时随机
        top_desire = active[0].desire_value
        tops = [a for a in active if a.desire_value == top_desire]

        # 主持人优先
        hosts = [a for a in tops if a.__class__.__name__ == "HostAgent"]
        if hosts:
            return hosts[0]

        # 随机选择
        return random.choice(tops) if tops else None
