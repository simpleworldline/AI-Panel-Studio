"""WebSocket 端点 — 对齐 API_CONTRACT.md §3"""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.services.discussion_manager import get_or_create_bus, get_runner

router = APIRouter()


@router.websocket("/ws/discussions/{discussion_id}")
async def ws_discussion(
    websocket: WebSocket,
    discussion_id: str,
    session_id: str = Query("anonymous"),
):
    await websocket.accept()

    bus = get_or_create_bus(discussion_id)
    bus.add_client(websocket)

    # 连接时推送当前状态快照
    runner = get_runner(discussion_id)
    if runner:
        import asyncio
        await websocket.send_text(json.dumps({
            "type": "initial_snapshot",
            "data": {
                "discussion_id": discussion_id,
                "status": runner._status,
                "current_round": runner.current_round,
                "total_utterances": runner.total_utterances,
                "transcript": runner.transcript,
                "consensus": runner.consensus_items,
                "disagreements": runner.disagreement_items,
            },
        }, ensure_ascii=False))

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            cmd_type = msg.get("type", "")
            runner = get_runner(discussion_id)

            if cmd_type == "advance" and runner:
                await runner._run_one_round()
            elif cmd_type == "pause" and runner:
                await runner.pause()
            elif cmd_type == "resume" and runner:
                await runner.resume()
            elif cmd_type == "end" and runner:
                await runner.force_end()
    except WebSocketDisconnect:
        pass
    finally:
        bus.remove_client(websocket)
