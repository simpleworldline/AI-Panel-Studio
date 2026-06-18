"""Runner Registry — 管理活跃的 DiscussionRunner 实例"""

import asyncio
from typing import Dict

from app.agents.discussion_runner import DiscussionRunner


class RunnerRegistry:
    """全局 Runner 注册表 — 每个活跃讨论对应一个 Runner

    提供 REST API 端和 WebSocket 端共享引用：
    - REST 端: start/pause/resume/end 控制
    - WebSocket 端: broadcast 事件推送
    """

    def __init__(self):
        self._runners: Dict[str, DiscussionRunner] = {}

    def create_runner(self, discussion_id: str, ws_manager) -> DiscussionRunner:
        """创建 Runner 并注册"""
        runner = DiscussionRunner(discussion_id, ws_manager)
        self._runners[discussion_id] = runner
        return runner

    def get(self, discussion_id: str) -> DiscussionRunner | None:
        return self._runners.get(discussion_id)

    def remove(self, discussion_id: str):
        self._runners.pop(discussion_id, None)

    def is_running(self, discussion_id: str) -> bool:
        runner = self._runners.get(discussion_id)
        return runner is not None and runner.is_running()


# 全局单例
runner_registry = RunnerRegistry()
