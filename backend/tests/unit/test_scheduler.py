"""
TDD: Scheduler — 欲望值仲裁器单元测试
依据: BACKEND_STRUCTURE.md §3.2
"""

import pytest


# 模拟 Agent 用于测试
class MockAgent:
    def __init__(self, desire: float, is_host: bool = False, name: str = "test"):
        self.desire_value = desire
        self._is_host = is_host
        self.name = name
        self.focus_summary = f"Focus {desire}"
        self.rounds_silent = 0

    @property
    def __class_name__(self) -> str:
        return "HostAgent" if self._is_host else "MockAgent"


@pytest.fixture
def host_agent():
    return MockAgent(0.8, is_host=True, name="host")


@pytest.fixture
def expert_agent():
    return MockAgent(0.7, is_host=False, name="expert")


class TestScheduler:
    def test_select_highest_desire(self):
        """欲望值最高者获得发言权"""
        from app.agents.scheduler import Scheduler
        import asyncio

        agents = [
            MockAgent(0.3),
            MockAgent(0.9),
            MockAgent(0.5),
        ]
        winner = asyncio.run(Scheduler.select_speaker(agents))
        assert winner is not None
        assert winner.desire_value == 0.9

    def test_host_wins_on_tie(self):
        """欲望值相等时主持人优先"""
        from app.agents.scheduler import Scheduler
        import asyncio

        # 创建 __name__=="HostAgent" 的动态子类
        HostAgentClass = type("HostAgent", (MockAgent,), {})

        agents = [
            MockAgent(0.8, name="expert1"),
            HostAgentClass(0.8, is_host=True, name="host"),
            MockAgent(0.8, name="expert2"),
        ]
        winner = asyncio.run(Scheduler.select_speaker(agents))
        assert winner is not None
        assert winner.desire_value == 0.8
        assert winner._is_host is True

    def test_no_agent_above_threshold(self):
        """所有欲望值低于 0.3 时无人发言"""
        from app.agents.scheduler import Scheduler
        import asyncio

        agents = [
            MockAgent(0.1),
            MockAgent(0.2),
        ]
        winner = asyncio.run(Scheduler.select_speaker(agents))
        assert winner is None

    def test_empty_agents(self):
        """空列表返回 None"""
        from app.agents.scheduler import Scheduler
        import asyncio

        winner = asyncio.run(Scheduler.select_speaker([]))
        assert winner is None

    def test_single_agent_selected(self):
        """单个 Agent 直接选中"""
        from app.agents.scheduler import Scheduler
        import asyncio

        agents = [MockAgent(0.5)]
        winner = asyncio.run(Scheduler.select_speaker(agents))
        assert winner is not None
        assert winner.desire_value == 0.5

    def test_multiple_ties_random(self):
        """同分非主持随机选择（验证不会崩溃，且结果在候选中）"""
        from app.agents.scheduler import Scheduler
        import asyncio

        agents = [
            MockAgent(0.6, name="A"),
            MockAgent(0.6, name="B"),
            MockAgent(0.6, name="C"),
        ]
        # Run multiple times to verify selection is among tied agents
        for _ in range(10):
            winner = asyncio.run(Scheduler.select_speaker(agents))
            assert winner is not None
            assert winner.desire_value == 0.6
            assert winner.name in ("A", "B", "C")
