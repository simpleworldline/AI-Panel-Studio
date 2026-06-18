"""讨论管理器 — 连接 REST API / WebSocket / DiscussionRunner

负责:
- 创建并存储 DiscussionRunner 实例
- 后台运行讨论
- WebSocket EventBus 注册
"""

import asyncio
from app.agents.llm_client import LLMClient
from app.agents.host_agent import HostAgent
from app.agents.expert_agent import ExpertAgent
from app.agents.observer_agent import ObserverAgent
from app.agents.scheduler import Scheduler
from app.agents.discussion_runner import DiscussionRunner
from app.config import settings


class WebSocketEventBus:
    """将讨论事件广播到所有连接的 WebSocket 客户端"""

    def __init__(self, discussion_id: str):
        self.discussion_id = discussion_id
        self._clients: list = []

    def add_client(self, ws):
        self._clients.append(ws)

    def remove_client(self, ws):
        self._clients = [c for c in self._clients if c is not ws]

    async def broadcast(self, event_type: str, data: dict):
        import json
        payload = json.dumps({"type": event_type, "data": data}, ensure_ascii=False)
        dead = []
        for ws in self._clients:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._clients.remove(ws)


# 全局注册表: discussion_id → {bus, runner, task}
_active: dict[str, dict] = {}


def get_or_create_bus(discussion_id: str) -> WebSocketEventBus:
    if discussion_id not in _active:
        _active[discussion_id] = {"bus": WebSocketEventBus(discussion_id), "runner": None, "task": None}
    return _active[discussion_id]["bus"]


def get_runner(discussion_id: str):
    entry = _active.get(discussion_id)
    return entry["runner"] if entry else None


def get_entry(discussion_id: str):
    return _active.get(discussion_id)


async def start_discussion_runner(discussion_id: str, topic: str, panel: list[dict], max_rounds: int | None = None):
    """创建 DiscussionRunner 并后台运行"""
    # 分离 host 和 experts
    host_data = None
    experts_data = []
    for m in panel:
        if m["role"] == "host":
            host_data = m
        else:
            experts_data.append(m)

    if not host_data:
        raise ValueError("阵容中缺少主持人")

    # 创建 LLM Client
    llm = LLMClient(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        max_retries=settings.llm_max_retries,
    )

    # 创建 agents
    host = HostAgent(
        member_id=host_data["id"],
        name=host_data["name"],
        title=host_data["title"],
        stance=host_data["stance"],
        color=host_data["color"],
        llm_client=llm,
    )

    experts = []
    for e in experts_data:
        expert = ExpertAgent(
            member_id=e["id"],
            name=e["name"],
            title=e["title"],
            stance=e["stance"],
            color=e["color"],
            llm_client=llm,
        )
        experts.append(expert)

    observer = ObserverAgent(
        member_id="observer",
        name="独立观察员",
        llm_client=llm,
    )

    scheduler = Scheduler()

    bus = get_or_create_bus(discussion_id)

    runner = DiscussionRunner(
        discussion_id=discussion_id,
        host=host,
        experts=experts,
        observer=observer,
        scheduler=scheduler,
        event_bus=bus,
        max_rounds=max_rounds,
        auto_end_threshold=settings.auto_end_threshold,
    )

    # 存储
    _active[discussion_id] = {
        "bus": bus,
        "runner": runner,
        "task": None,
    }

    # 后台启动
    task = asyncio.create_task(runner.run())
    _active[discussion_id]["task"] = task

    # 推送初始快照到已连接的 WS 客户端
    await bus.broadcast("initial_snapshot", {
        "discussion_id": discussion_id,
        "status": "live",
        "current_round": 0,
        "total_utterances": 0,
        "transcript": [],
        "consensus": [],
        "disagreements": [],
    })

    return runner
