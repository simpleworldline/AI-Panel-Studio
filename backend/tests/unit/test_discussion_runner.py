"""Phase 6 — discussion_runner.py 测试 (RED)

验证讨论运行引擎的完整生命周期:
- 开场 → N 轮发言 → 总结 → 结束
- 暂停/继续
- 手动推进
- 自动结束条件 (max_rounds / no_consensus)
"""

import pytest
import asyncio
from tests.conftest import MockLLMClient


# ============================================================
# Test Helpers
# ============================================================

def make_mock_panel():
    """创建 mock 嘉宾阵容: 1 主持 + 2 专家"""
    host = FakeAgent("host-1", "host", "张明", "AI伦理学家")
    expert1 = FakeAgent("expert-1", "expert", "李研究员", "认知科学研究所高级研究员")
    expert2 = FakeAgent("expert-2", "expert", "王博士", "计算机科学教授")
    return host, [expert1, expert2]


class FakeAgent:
    """符合 Scheduler AgentLike 接口"""
    def __init__(self, member_id, role, name, title, desire=0.5, focus_time=1000.0):
        self.member_id = member_id
        self.role = role
        self.name = name
        self.title = title
        self.desire = desire
        self.focus_time = focus_time
        self._utterance = "测试发言内容。"
        self._focus = "正在关注讨论"
        self._utterance_gen = None

    def set_utterance(self, text):
        self._utterance = text

    def set_stream_tokens(self, tokens):
        self._utterance_gen = tokens

    def calculate_desire(self, transcript, current_focus, **kw):
        return self.desire

    def get_focus_summary(self, transcript, current_focus, **kw):
        return self._focus

    async def generate_utterance(self, transcript, current_focus, **kw):
        if self._utterance_gen:
            for t in self._utterance_gen:
                yield t
            self._utterance_gen = None
        else:
            for ch in self._utterance:
                yield ch

    def generate_utterance_sync(self, transcript, current_focus, **kw):
        return self._utterance


class FakeObserver:
    """模拟独立观察员"""
    def __init__(self):
        self.responses = []  # 按调用顺序返回

    def add_response(self, action="none", ctype="consensus", title="", desc="", confidence=0.0):
        self.responses.append({
            "action": action, "type": ctype,
            "title": title, "description": desc, "confidence": confidence,
        })

    def analyze_sync(self, transcript, existing_consensus, latest_utterance):
        if not self.responses:
            return {"action": "none", "type": "consensus", "title": "", "description": "", "confidence": 0.0}
        return self.responses.pop(0)

    async def analyze(self, transcript, existing_consensus, latest_utterance):
        return self.analyze_sync(transcript, existing_consensus, latest_utterance)


class FakeEventBus:
    """事件总线 — 记录所有广播事件"""
    def __init__(self):
        self.events = []

    async def broadcast(self, event_type, data):
        self.events.append({"type": event_type, "data": data})


# ============================================================
# 完整生命周期
# ============================================================

class TestFullLifecycle:
    """开场 → 3 轮 → 总结 → 结束"""

    async def test_complete_discussion_flow(self):
        from app.agents.discussion_runner import DiscussionRunner
        from app.agents.scheduler import Scheduler

        host, experts = make_mock_panel()
        host.set_utterance("各位专家，欢迎来到今天的AI圆桌讨论。")
        experts[0].set_utterance("我认为AI意识应从功能层面定义。")
        experts[1].set_utterance("我赞同功能主义，但伦理边界不可忽视。")

        observer = FakeObserver()
        observer.add_response("created", "consensus", "功能主义共识", "一致同意从功能层面定义", 0.92)
        observer.add_response("none")

        bus = FakeEventBus()
        runner = DiscussionRunner(
            discussion_id="d-001",
            host=host,
            experts=experts,
            observer=observer,
            scheduler=Scheduler(),
            event_bus=bus,
            max_rounds=2,
            auto_end_threshold=3,
        )

        await runner.run()

        # 验证事件序列
        event_types = [e["type"] for e in bus.events]
        assert "expert_status" in event_types
        assert "utterance_token" in event_types or "utterance_complete" in event_types
        assert "discussion_ended" in event_types

    async def test_opening_utterance_emitted(self):
        from app.agents.discussion_runner import DiscussionRunner
        from app.agents.scheduler import Scheduler

        host, experts = make_mock_panel()
        host.set_utterance("欢迎来到讨论。")

        bus = FakeEventBus()
        runner = DiscussionRunner(
            discussion_id="d-001",
            host=host,
            experts=experts,
            observer=FakeObserver(),
            scheduler=Scheduler(),
            event_bus=bus,
            max_rounds=0,
            auto_end_threshold=3,
        )

        await runner.run()

        # 第一条 utterance_complete 应为主持人开场白
        utterances = [e for e in bus.events if e["type"] == "utterance_complete"]
        assert len(utterances) >= 1
        assert utterances[0]["data"]["member_id"] == "host-1"


# ============================================================
# 结束条件
# ============================================================

class TestEndConditions:
    """max_rounds / no_consensus 自动结束"""

    async def test_max_rounds_triggers_end(self):
        from app.agents.discussion_runner import DiscussionRunner
        from app.agents.scheduler import Scheduler

        host, experts = make_mock_panel()
        bus = FakeEventBus()
        runner = DiscussionRunner(
            discussion_id="d-001",
            host=host, experts=experts,
            observer=FakeObserver(),
            scheduler=Scheduler(),
            event_bus=bus,
            max_rounds=2,
            auto_end_threshold=10,  # 不触发无共识结束
        )

        await runner.run()

        ended = [e for e in bus.events if e["type"] == "discussion_ended"]
        assert len(ended) == 1
        assert "max_rounds" in ended[0]["data"]["end_reason"] or ended[0]["data"]["end_reason"] in ("max_rounds",)

    async def test_no_consensus_triggers_end(self):
        from app.agents.discussion_runner import DiscussionRunner
        from app.agents.scheduler import Scheduler

        host, experts = make_mock_panel()
        observer = FakeObserver()
        # 每轮都返回 none → rounds_without_consensus 递增 → 触发自动结束
        for _ in range(10):
            observer.add_response("none")

        bus = FakeEventBus()
        runner = DiscussionRunner(
            discussion_id="d-001",
            host=host, experts=experts,
            observer=observer,
            scheduler=Scheduler(),
            event_bus=bus,
            max_rounds=50,
            auto_end_threshold=2,  # 仅 2 轮无共识即结束
        )

        await runner.run()
        assert runner.rounds_without_consensus >= runner.auto_end_threshold


# ============================================================
# 暂停 / 继续
# ============================================================

class TestPauseResume:
    """暂停后阻塞，继续后恢复"""

    async def test_pause_stops_loop(self):
        from app.agents.discussion_runner import DiscussionRunner
        from app.agents.scheduler import Scheduler

        host, experts = make_mock_panel()
        bus = FakeEventBus()
        runner = DiscussionRunner(
            discussion_id="d-001",
            host=host, experts=experts,
            observer=FakeObserver(),
            scheduler=Scheduler(),
            event_bus=bus,
            max_rounds=5,
            auto_end_threshold=10,
        )

        # 在另一 task 中运行，立即暂停
        import asyncio
        async def run_and_pause():
            await asyncio.sleep(0.05)  # 让 run() 至少走一轮
            await runner.pause()

        task = asyncio.create_task(runner.run())
        await asyncio.sleep(0.03)
        await runner.pause()
        await task  # run() 应在暂停后结束（因为暂停设了 stop 标志）

        paused_events = [e for e in bus.events if e["type"] == "discussion_paused"]
        assert len(paused_events) >= 1


# ============================================================
# 手动推进
# ============================================================

class TestManualAdvance:
    """advance_round() 手动触发一轮"""

    async def test_advance_round_triggers_one_utterance(self):
        from app.agents.discussion_runner import DiscussionRunner
        from app.agents.scheduler import Scheduler

        host, experts = make_mock_panel()
        host.desire = 0.0  # 让专家当选
        experts[0].desire = 0.9
        experts[1].desire = 0.5
        experts[0].set_utterance("手动推进的发言。")

        bus = FakeEventBus()
        runner = DiscussionRunner(
            discussion_id="d-001",
            host=host, experts=experts,
            observer=FakeObserver(),
            scheduler=Scheduler(),
            event_bus=bus,
            max_rounds=1,
            auto_end_threshold=10,
        )

        await runner._start_opening()
        count_before = len([e for e in bus.events if e["type"] == "utterance_complete"])
        await runner._run_one_round()
        count_after = len([e for e in bus.events if e["type"] == "utterance_complete"])
        assert count_after > count_before


# ============================================================
# 强制结束
# ============================================================

class TestForceEnd:
    """force_end() 立即终止"""

    async def test_force_end_sets_stop_flag_and_emits_user_ended(self):
        from app.agents.discussion_runner import DiscussionRunner
        from app.agents.scheduler import Scheduler

        host, experts = make_mock_panel()
        bus = FakeEventBus()
        runner = DiscussionRunner(
            discussion_id="d-001",
            host=host, experts=experts,
            observer=FakeObserver(),
            scheduler=Scheduler(),
            event_bus=bus,
            max_rounds=10,
            auto_end_threshold=10,
        )

        await runner.force_end()
        assert runner._stop_flag.is_set()
        await runner._emit_ended(runner._end_reason())
        ended = [e for e in bus.events if e["type"] == "discussion_ended"]
        assert len(ended) == 1
        assert ended[0]["data"]["end_reason"] == "user_ended"

    async def test_run_stops_on_force_end(self):
        from app.agents.discussion_runner import DiscussionRunner
        from app.agents.scheduler import Scheduler

        host, experts = make_mock_panel()
        bus = FakeEventBus()
        runner = DiscussionRunner(
            discussion_id="d-001",
            host=host, experts=experts,
            observer=FakeObserver(),
            scheduler=Scheduler(),
            event_bus=bus,
            max_rounds=50,
            auto_end_threshold=50,
        )

        # run in background, force-end after short delay
        task = asyncio.create_task(runner.run())
        await asyncio.sleep(0.01)
        await runner.force_end()
        await asyncio.wait_for(task, timeout=1.0)

        # 只要有 discussion_ended 事件即通过
        ended = [e for e in bus.events if e["type"] == "discussion_ended"]
        assert len(ended) >= 1
