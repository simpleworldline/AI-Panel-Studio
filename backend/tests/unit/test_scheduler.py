"""Phase 3 — scheduler.py 测试 (RED)

欲望值调度仲裁器测试。
决断链: desire_value ↓ → focus_distance ↑ → random
主持人同分时优先于专家。
"""

import random
import pytest


# ============================================================
# Helper — build a simple agent-like struct
# ============================================================

class FakeAgent:
    """模拟 Agent 的最小接口"""
    def __init__(self, member_id: str, role: str, desire: float, focus_time: float):
        self.member_id = member_id
        self.role = role          # "host" | "expert"
        self.desire = desire      # 0.00 - 1.00
        self.focus_time = focus_time  # epoch seconds (越大越近 = 关注点越新)


# ============================================================
# 基本欲望值排序
# ============================================================

class TestDesireSort:
    """欲望值最高者当选"""

    def test_highest_desire_wins(self):
        from app.agents.scheduler import Scheduler
        agents = [
            FakeAgent("a", "expert", 0.55, 100.0),
            FakeAgent("b", "expert", 0.87, 100.0),
            FakeAgent("c", "expert", 0.32, 100.0),
        ]
        s = Scheduler()
        winner = s.select_speaker(agents)
        assert winner.member_id == "b"

    def test_single_agent_wins(self):
        from app.agents.scheduler import Scheduler
        agents = [FakeAgent("a", "expert", 0.42, 100.0)]
        s = Scheduler()
        winner = s.select_speaker(agents)
        assert winner.member_id == "a"


# ============================================================
# 第一决胜点: 欲望值相同 → 关注点时间距离
# ============================================================

class TestFocusTimeTiebreak:
    """同分时，关注点时间更近的当选"""

    def test_newer_focus_wins_on_tie(self):
        from app.agents.scheduler import Scheduler
        agents = [
            FakeAgent("a", "expert", 0.80, 1000.0),  # focus 较旧
            FakeAgent("b", "expert", 0.80, 2000.0),  # focus 较新
        ]
        s = Scheduler()
        winner = s.select_speaker(agents)
        assert winner.member_id == "b"

    def test_focus_time_decides_before_random(self):
        from app.agents.scheduler import Scheduler
        # 三者同 desire，但 focus_time 不同
        agents = [
            FakeAgent("oldest", "expert", 0.75, 500.0),
            FakeAgent("newest", "expert", 0.75, 3000.0),
            FakeAgent("mid", "expert", 0.75, 1500.0),
        ]
        s = Scheduler()
        winner = s.select_speaker(agents)
        assert winner.member_id == "newest"


# ============================================================
# 第二决胜点: 同分同时间 → 随机
# ============================================================

class TestRandomTiebreak:
    """完全相同 → 随机选择"""

    def test_random_when_all_equal(self, monkeypatch):
        from app.agents.scheduler import Scheduler
        agents = [
            FakeAgent("a", "expert", 0.70, 100.0),
            FakeAgent("b", "expert", 0.70, 100.0),
            FakeAgent("c", "expert", 0.70, 100.0),
        ]
        s = Scheduler()

        # 固定 random 返回 0 → 选第一个
        monkeypatch.setattr(s, "_random_index", lambda n: 0)
        winner = s.select_speaker(agents)
        assert winner.member_id == "a"

        # 固定 random 返回 n-1 → 选最后一个
        monkeypatch.setattr(s, "_random_index", lambda n: n - 1)
        winner = s.select_speaker(agents)
        assert winner.member_id == "c"

    def test_random_uses_same_seed_per_call(self):
        """确认随机只在同分同 time 的 subset 内随机"""
        from app.agents.scheduler import Scheduler
        agents = [
            FakeAgent("high", "expert", 0.90, 100.0),   # 最高分，不参与随机
            FakeAgent("low_a", "expert", 0.50, 200.0),
            FakeAgent("low_b", "expert", 0.50, 200.0),
        ]
        s = Scheduler()
        winner = s.select_speaker(agents)
        assert winner.member_id == "high"  # 最高分直接胜出，不触发随机


# ============================================================
# 主持人同分优先
# ============================================================

class TestHostPriority:
    """主持人同分时优先于专家"""

    def test_host_wins_on_tie_with_expert(self):
        from app.agents.scheduler import Scheduler
        agents = [
            FakeAgent("host", "host", 0.80, 100.0),
            FakeAgent("expert", "expert", 0.80, 100.0),
        ]
        s = Scheduler()
        winner = s.select_speaker(agents)
        assert winner.member_id == "host"

    def test_expert_wins_if_higher_desire_than_host(self):
        from app.agents.scheduler import Scheduler
        agents = [
            FakeAgent("host", "host", 0.75, 100.0),
            FakeAgent("expert", "expert", 0.85, 100.0),
        ]
        s = Scheduler()
        winner = s.select_speaker(agents)
        assert winner.member_id == "expert"

    def test_host_priority_applies_per_tie_group(self):
        """主持人优先仅在 tie group 内生效，不同 desire 组无效"""
        from app.agents.scheduler import Scheduler
        agents = [
            FakeAgent("expert_high", "expert", 0.90, 100.0),    # 最高
            FakeAgent("host_mid", "host", 0.80, 120.0),          # 中
            FakeAgent("expert_mid", "expert", 0.80, 100.0),      # 中, focus 旧
        ]
        s = Scheduler()
        winner = s.select_speaker(agents)
        # 0.90 最高 → expert_high 胜出; host 在 0.80 组的优先只在同分有效
        assert winner.member_id == "expert_high"

    def test_host_wins_same_desire_even_if_focus_older(self):
        """主持人同分时无视 focus_time 差异"""
        from app.agents.scheduler import Scheduler
        agents = [
            FakeAgent("host", "host", 0.75, 500.0),    # focus 更旧
            FakeAgent("expert", "expert", 0.75, 2000.0),  # focus 更新
        ]
        s = Scheduler()
        winner = s.select_speaker(agents)
        assert winner.member_id == "host"  # 主持人优先 > focus_time


# ============================================================
# 边界条件
# ============================================================

class TestEdgeCases:
    """异常与边界"""

    def test_empty_list_raises(self):
        from app.agents.scheduler import Scheduler
        s = Scheduler()
        with pytest.raises(ValueError):
            s.select_speaker([])

    def test_multiple_hosts_self_resolve(self):
        """多个主持人间用 focus_time 决断 (极端情况)"""
        from app.agents.scheduler import Scheduler
        # 两个 host 同 desire — 按正常规则用 focus_time
        agents = [
            FakeAgent("host_older", "host", 0.80, 500.0),
            FakeAgent("host_newer", "host", 0.80, 2000.0),
        ]
        s = Scheduler()
        winner = s.select_speaker(agents)
        assert winner.member_id == "host_newer"
