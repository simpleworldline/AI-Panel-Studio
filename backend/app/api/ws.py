"""API_CONTRACT.md §3 — WebSocket 端点"""

import asyncio
import json
import time

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.discussion import Discussion
from app.models.panel_member import PanelMember
from app.services.runner_registry import runner_registry

router = APIRouter()


class ConnectionManager:
    """管理 WebSocket 连接"""

    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}  # discussion_id → [ws, ...]

    async def connect(self, discussion_id: str, ws: WebSocket):
        await ws.accept()
        self._connections.setdefault(discussion_id, []).append(ws)

    def disconnect(self, discussion_id: str, ws: WebSocket):
        conns = self._connections.get(discussion_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, discussion_id: str, event: dict):
        conns = self._connections.get(discussion_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(discussion_id, ws)


manager = ConnectionManager()


@router.websocket("/ws/discussions/{discussion_id}")
async def ws_discussion(
    websocket: WebSocket,
    discussion_id: str,
    session_id: str = Query(""),
):
    """讨论 WebSocket 连接 — 连接/权限校验/事件路由"""
    # 验证讨论存在
    from app.db.session import async_session_factory

    async with async_session_factory() as db:
        d = await db.get(Discussion, discussion_id)
        if d is None:
            await websocket.close(code=4004, reason="讨论不存在")
            return

        is_creator = (d.creator_session_id == session_id)
        await manager.connect(discussion_id, websocket)

        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                event_type = data.get("type")
                if event_type not in ("advance", "pause", "resume", "end"):
                    continue

                # 权限校验：控制指令仅创建者可发送
                if not is_creator:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": "非创建者无权发送控制指令"},
                    })
                    continue

                # 广播控制事件 (互相同步 WS + REST)
                runner = runner_registry.get(discussion_id)
                if event_type == "advance":
                    if runner:
                        import asyncio
                        asyncio.create_task(runner.resume())
                    await manager.broadcast(discussion_id, {
                        "type": "discussion_control",
                        "data": {"action": "advance", "discussion_id": discussion_id},
                    })
                elif event_type == "pause":
                    d.status = "paused"
                    await db.commit()
                    if runner:
                        import asyncio
                        asyncio.create_task(runner.pause())
                    await manager.broadcast(discussion_id, {
                        "type": "discussion_paused",
                        "data": {"discussion_id": discussion_id, "timestamp": _now()},
                    })
                elif event_type == "resume":
                    d.status = "live"
                    await db.commit()
                    if runner:
                        import asyncio
                        asyncio.create_task(runner.resume())
                    await manager.broadcast(discussion_id, {
                        "type": "discussion_resumed",
                        "data": {"discussion_id": discussion_id, "timestamp": _now()},
                    })
                elif event_type == "end":
                    d.status = "ended"
                    await db.commit()
                    if runner:
                        await runner.stop()
                    await manager.broadcast(discussion_id, {
                        "type": "discussion_ended",
                        "data": {
                            "discussion_id": discussion_id,
                            "end_reason": "user_ended",
                            "total_rounds": d.current_round,
                            "total_utterances": 0,
                            "ended_at": _now(),
                        },
                    })

        except WebSocketDisconnect:
            pass
        finally:
            manager.disconnect(discussion_id, websocket)


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
