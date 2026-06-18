"""API_CONTRACT.md §3 — WebSocket endpoint with initial snapshot on connect"""

import asyncio
import json

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.models.discussion import Discussion
from app.models.panel_member import PanelMember
from app.models.utterance import Utterance
from app.services.runner_registry import runner_registry

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections per discussion"""

    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

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


async def send_initial_snapshot(ws: WebSocket, discussion_id: str):
    """Send current discussion state to newly connected client"""
    from app.db.database import async_session_factory

    async with async_session_factory() as db:
        # Discussion
        d = await db.get(Discussion, discussion_id)
        if d is None:
            return

        # Panel members
        members_result = await db.execute(
            select(PanelMember)
            .where(PanelMember.discussion_id == discussion_id)
            .order_by(PanelMember.sort_order)
        )
        panel = [
            {"id": m.id, "name": m.name, "title": m.title,
             "role": m.role, "stance": m.stance, "color": m.color}
            for m in members_result.scalars().all()
        ]

        # Utterances with member info
        utter_result = await db.execute(
            select(Utterance)
            .where(Utterance.discussion_id == discussion_id)
            .order_by(Utterance.sequence_num)
        )
        utterances = utter_result.scalars().all()

        # Look up member names
        member_ids = {u.panel_member_id for u in utterances}
        member_map = {}
        if member_ids:
            m_result = await db.execute(
                select(PanelMember).where(PanelMember.id.in_(member_ids))
            )
            for m in m_result.scalars().all():
                member_map[m.id] = m

        transcript = [
            {"id": u.id, "panelMemberId": u.panel_member_id,
             "memberName": member_map[u.panel_member_id].name if u.panel_member_id in member_map else "Unknown",
             "memberTitle": member_map[u.panel_member_id].title if u.panel_member_id in member_map else "",
             "memberColor": member_map[u.panel_member_id].color if u.panel_member_id in member_map else "#000",
             "content": u.content, "utteranceType": u.utterance_type,
             "sequenceNum": u.sequence_num, "roundNum": u.round_num,
             "createdAt": u.created_at}
            for u in utterances
        ]

        db.commit()

    await ws.send_json({
        "type": "initial_snapshot",
        "data": {
            "discussionId": discussion_id,
            "status": d.status,
            "currentRound": d.current_round,
            "totalUtterances": len(transcript),
            "transcript": transcript,
            "panel": panel,
            "consensus": [],
            "disagreements": [],
        },
    })


@router.websocket("/ws/discussions/{discussion_id}")
async def ws_discussion(
    websocket: WebSocket,
    discussion_id: str,
    session_id: str = Query(""),
):
    """Discussion WebSocket — connect, permission check, event routing"""
    from app.db.database import async_session_factory

    async with async_session_factory() as db:
        d = await db.get(Discussion, discussion_id)
        if d is None:
            await websocket.close(code=4004, reason="discussion not found")
            return
        db.commit()

    is_creator = (d.creator_session_id == session_id)
    await manager.connect(discussion_id, websocket)

    # Send initial snapshot so client sees current state immediately
    try:
        await send_initial_snapshot(websocket, discussion_id)
    except Exception:
        pass

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

            if not is_creator:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "Only the creator can send control commands"},
                })
                continue

            runner = runner_registry.get(discussion_id)

            if event_type == "advance":
                if runner:
                    runner.force_step()
                await manager.broadcast(discussion_id, {
                    "type": "discussion_control",
                    "data": {"action": "advance", "discussionId": discussion_id},
                })

            elif event_type == "pause":
                if runner:
                    runner.pause()
                await manager.broadcast(discussion_id, {
                    "type": "discussion_paused",
                    "data": {"discussionId": discussion_id, "timestamp": _now()},
                })

            elif event_type == "resume":
                if runner:
                    runner.resume()
                await manager.broadcast(discussion_id, {
                    "type": "discussion_resumed",
                    "data": {"discussionId": discussion_id, "timestamp": _now()},
                })

            elif event_type == "end":
                if runner:
                    runner.stop()
                await manager.broadcast(discussion_id, {
                    "type": "discussion_ended",
                    "data": {
                        "discussionId": discussion_id,
                        "endReason": "user_ended",
                        "totalRounds": d.current_round,
                        "totalUtterances": 0,
                        "endedAt": _now(),
                    },
                })

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(discussion_id, websocket)


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
