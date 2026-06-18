"""讨论运行引擎 — Agent-Mediator 模式核心调度器

对齐 BACKEND_STRUCTURE.md §3.4 调度循环:
  emit_opening → [while not end: pause? → schedule → speak → observe → inc_round]
  → host_summary → end_discussion
"""

import asyncio
import time
import uuid
from datetime import datetime, timezone


class DiscussionRunner:
    """管理讨论完整生命周期，协调 Agent / Scheduler / Observer / EventBus"""

    def __init__(
        self,
        discussion_id: str,
        host,                    # HostAgent
        experts: list,           # list[ExpertAgent]
        observer,                # ObserverAgent
        scheduler,               # Scheduler
        event_bus,               # 推送 WS 事件
        max_rounds: int | None = None,
        auto_end_threshold: int = 3,
    ):
        self.discussion_id = discussion_id
        self.host = host
        self.experts = experts
        self.observer = observer
        self.scheduler = scheduler
        self.event_bus = event_bus
        self.max_rounds = max_rounds
        self.auto_end_threshold = auto_end_threshold

        self.current_round = 0
        self.rounds_without_consensus = 0
        self.total_utterances = 0
        self.transcript: list[dict] = []
        self.consensus_items: list[dict] = []
        self.disagreement_items: list[dict] = []

        # 追踪每位 agent 的沉默轮次
        self._silence_counter: dict[str, int] = {}

        self._paused = asyncio.Event()
        self._paused.set()  # 初始不暂停
        self._stop_flag = asyncio.Event()
        self._status = "live"

    # ================================================================
    # 公共控制接口
    # ================================================================

    async def run(self):
        """完整运行讨论 (异步)"""
        try:
            await self._start_opening()
            while not self._should_end():
                await self._check_pause()
                if self._stop_flag.is_set():
                    break
                await self._run_one_round()
                self.current_round += 1
            await self._closing()
        finally:
            await self._emit_ended("user_ended" if self._stop_flag.is_set() else self._end_reason())

    async def pause(self):
        self._paused.clear()
        self._status = "paused"
        await self._broadcast("discussion_paused", {
            "discussion_id": self.discussion_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def resume(self):
        self._paused.set()
        self._status = "live"
        await self._broadcast("discussion_resumed", {
            "discussion_id": self.discussion_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def force_end(self):
        self._stop_flag.set()
        self._paused.set()  # 解除暂停阻塞
        self._status = "ended"

    # ================================================================
    # 内部
    # ================================================================

    async def _start_opening(self):
        """主持人开场白"""
        # 初始化沉默计数器
        for a in [self.host] + self.experts:
            self._silence_counter[a.member_id] = 0

        # 广播全部嘉宾初始状态 (专家=idle, 主持人=preparing)
        for e in self.experts:
            await self._broadcast_expert_status(e, "idle",
                e.get_focus_summary(self.transcript, "等待主持人开场"))
        await self._broadcast_expert_status(self.host, "preparing",
            self.host.get_focus_summary(self.transcript, "准备开场"))

        await self._speak(self.host, "开场", "opening")
        # opening 后所有非主持 experts silence +1
        for e in self.experts:
            self._silence_counter[e.member_id] = 1
        await self._observer_analyze()

    async def _run_one_round(self):
        """执行一轮: schedule → speak → observe"""
        agents = [self.host] + self.experts

        # 获取最新发言的焦点话题
        last_focus = self.transcript[-1]["content"][:80] if self.transcript else "讨论进行中"

        for a in agents:
            silent_rounds = self._silence_counter.get(a.member_id, 0)
            a.calculate_desire(self.transcript, last_focus, rounds_since_last_spoke=silent_rounds)

        winner = self.scheduler.select_speaker(agents)

        # 更新沉默计数器
        for a in agents:
            if a is winner:
                self._silence_counter[a.member_id] = 0
            else:
                self._silence_counter[a.member_id] = self._silence_counter.get(a.member_id, 0) + 1

        # 状态: selected agent → speaking, others → idle
        for a in agents:
            if a is winner:
                await self._broadcast_expert_status(a, "speaking", a.get_focus_summary(self.transcript, "发言中"))
            else:
                await self._broadcast_expert_status(a, "idle", a.get_focus_summary(self.transcript, "等待中"))

        await self._speak(winner, "讨论", "statement")
        await self._observer_analyze()

    async def _closing(self):
        """主持人总结 — 使用完整 transcript 作为上下文"""
        focus = "总结整场讨论"
        self.host.calculate_desire(self.transcript, focus, rounds_since_last_spoke=0, phase="closing")
        await self._broadcast_expert_status(self.host, "speaking", self.host.get_focus_summary(self.transcript, focus))
        await self._speak(self.host, focus, "summary", phase="closing")

    async def _speak(self, agent, focus, utterance_type, **kw):
        """让 agent 流式发言，逐 token 广播"""
        utterance_id = str(uuid.uuid4())

        # preparing
        await self._broadcast_expert_status(agent, "preparing", agent.get_focus_summary(self.transcript, focus))

        # speaking — 流式 token
        content = ""
        is_first = True
        try:
            async for token in agent.generate_utterance(self.transcript, focus, utterance_type=utterance_type, **kw):
                content += token
                await self._broadcast("utterance_token", {
                    "utterance_id": utterance_id,
                    "member_id": agent.member_id,
                    "member_name": agent.name,
                    "member_title": agent.title,
                    "member_color": getattr(agent, "color", "#FFFFFF"),
                    "token": token,
                    "sequence_num": self.total_utterances + 1,
                    "round_num": self.current_round,
                    "is_first": is_first,
                    "is_last": False,
                })
                is_first = False
        except Exception:
            pass  # 流式中断不阻塞

        # complete
        self.total_utterances += 1
        created_at = datetime.now(timezone.utc).isoformat()
        utterance_record = {
            "id": utterance_id,
            "member_id": agent.member_id,
            "member_name": agent.name,
            "member_title": agent.title,
            "member_color": getattr(agent, "color", "#FFFFFF"),
            "content": content,
            "utterance_type": utterance_type,
            "sequence_num": self.total_utterances,
            "round_num": self.current_round,
            "created_at": created_at,
        }
        self.transcript.append(utterance_record)

        await self._broadcast("utterance_complete", {
            "utterance_id": utterance_id,
            "member_id": agent.member_id,
            "member_name": agent.name,
            "member_title": agent.title,
            "member_color": getattr(agent, "color", "#FFFFFF"),
            "content": content,
            "utterance_type": utterance_type,
            "sequence_num": self.total_utterances,
            "round_num": self.current_round,
            "created_at": created_at,
        })

    async def _observer_analyze(self):
        """观察员分析最新发言"""
        if not self.transcript:
            return
        result = await self.observer.analyze(
            self.transcript, self.consensus_items + self.disagreement_items, self.transcript[-1]
        )
        action = result.get("action", "none")
        ctype = result.get("type", "consensus")

        if action in ("created", "updated", "resolved"):
            record = {
                "id": str(uuid.uuid4()),
                "type": ctype,
                "title": result.get("title", ""),
                "description": result.get("description", ""),
                "source_utterance_ids": [self.transcript[-1]["id"]],
                "confidence": result.get("confidence", 1.0),
                "is_resolved": action == "resolved" if ctype == "disagreement" else False,
                "round_num": self.current_round,
            }
            if ctype == "consensus":
                if action == "created":
                    self.consensus_items.append(record)
                elif action == "updated" and self.consensus_items:
                    self.consensus_items[-1] = record
            else:
                if action == "created":
                    self.disagreement_items.append(record)
                elif action == "updated" and self.disagreement_items:
                    self.disagreement_items[-1] = record
                elif action == "resolved":
                    for item in self.disagreement_items:
                        if item.get("title") == record["title"]:
                            item["is_resolved"] = True
                            break

            self.rounds_without_consensus = 0
            await self._broadcast("consensus_update", {"action": action, "record": record})
        else:
            self.rounds_without_consensus += 1

    async def _broadcast_expert_status(self, agent, status, focus_summary):
        """对专家/主持人广播状态"""
        desire = getattr(agent, "desire", 0.0)
        await self._broadcast("expert_status", {
            "member_id": agent.member_id,
            "member_name": agent.name,
            "member_color": getattr(agent, "color", "#FFFFFF"),
            "status": status,
            "focus_summary": focus_summary,
            "desire_value": desire,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def _broadcast(self, event_type, data):
        await self.event_bus.broadcast(event_type, data)

    async def _check_pause(self):
        """阻塞直到 _paused 被 set"""
        await self._paused.wait()

    def _should_end(self) -> bool:
        if self._stop_flag.is_set():
            return True
        if self.max_rounds is not None and self.current_round >= self.max_rounds:
            return True
        if self.rounds_without_consensus >= self.auto_end_threshold:
            return True
        return False

    def _end_reason(self) -> str:
        if self._stop_flag.is_set():
            return "user_ended"
        if self.max_rounds is not None and self.current_round >= self.max_rounds:
            return "max_rounds"
        if self.rounds_without_consensus >= self.auto_end_threshold:
            return "no_consensus"
        return "host_decided"

    async def _emit_ended(self, reason):
        await self._broadcast("discussion_ended", {
            "discussion_id": self.discussion_id,
            "end_reason": reason,
            "total_rounds": self.current_round,
            "total_utterances": self.total_utterances,
            "ended_at": datetime.now(timezone.utc).isoformat(),
        })
        self._status = "ended"
