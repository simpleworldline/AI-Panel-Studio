"""Runner Registry — 管理活跃的 DiscussionRunner 实例及其后台任务"""

import asyncio
import logging
from typing import Dict

from app.agents.discussion_runner import DiscussionRunner

logger = logging.getLogger("runner_registry")


class RunnerRegistry:
    """全局 Runner 注册表

    REST API 和 WebSocket 端点通过此注册表共享 Runner 引用：
    - REST: start/pause/resume/end
    - WebSocket: broadcast 事件推送
    - 保持 asyncio.Task 引用防止 GC 回收
    """

    def __init__(self):
        self._runners: Dict[str, DiscussionRunner] = {}
        self._tasks: Dict[str, asyncio.Task] = {}

    def create_runner(self, discussion_id: str, ws_manager) -> DiscussionRunner:
        """创建 Runner 并注册"""
        runner = DiscussionRunner(discussion_id, ws_manager)
        self._runners[discussion_id] = runner
        return runner

    def get(self, discussion_id: str) -> DiscussionRunner | None:
        return self._runners.get(discussion_id)

    def remove(self, discussion_id: str):
        self._runners.pop(discussion_id, None)
        task = self._tasks.pop(discussion_id, None)
        if task and not task.done():
            task.cancel()

    def is_running(self, discussion_id: str) -> bool:
        runner = self._runners.get(discussion_id)
        return runner is not None and runner.is_running()

    def set_task(self, discussion_id: str, task: asyncio.Task):
        """存储后台任务引用，防止 GC"""
        self._tasks[discussion_id] = task
        # 任务完成后自动清理
        task.add_done_callback(lambda t: self._on_task_done(discussion_id, t))

    def _on_task_done(self, discussion_id: str, task: asyncio.Task):
        """后台任务完成时清理"""
        self._tasks.pop(discussion_id, None)
        self._runners.pop(discussion_id, None)
        if task.exception():
            logger.error(f"Runner task for {discussion_id[:8]} failed: {task.exception()}")


# 全局单例
runner_registry = RunnerRegistry()
