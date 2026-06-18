"""Discussion management endpoints"""

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.database import async_session_factory
from app.schemas.discussion import DiscussionCreate
from app.schemas.common import ApiResponse
from app.services.discussion_service import DiscussionService, PermissionError, StateConflictError
from app.services.report_service import ReportService
from app.services.runner_registry import runner_registry
from app.api.ws import manager as ws_manager

logger = logging.getLogger("discussions_api")
router = APIRouter(prefix="/api/discussions", tags=["discussions"])


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@router.post("", status_code=201)
async def create_discussion(
    body: DiscussionCreate, x_session_id: str = Header(..., alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    d = await DiscussionService.create(db, topic=body.topic, creator_session_id=x_session_id,
                                        expert_count=body.expert_count, max_rounds=body.max_rounds)
    return ApiResponse(code=201, data={
        "id": d.id, "topic": d.topic, "expert_count": d.expert_count,
        "max_rounds": d.max_rounds, "status": d.status,
        "creator_session_id": d.creator_session_id,
        "current_round": d.current_round, "created_at": d.created_at,
    }, message="讨论创建成功")


@router.get("")
async def list_discussions(
    status: str | None = Query(None), page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db),
):
    result = await DiscussionService.list_discussions(db, status=status, page=page, page_size=page_size)
    return ApiResponse(code=200, data=result, message="success")


@router.get("/{discussion_id}")
async def get_discussion(discussion_id: str, db: AsyncSession = Depends(get_db)):
    detail = await DiscussionService.get_detail(db, discussion_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="讨论不存在")
    return ApiResponse(code=200, data=detail, message="success")


# ── Start (DB write + launch runner) ──
@router.post("/{discussion_id}/start")
async def start_discussion(
    discussion_id: str, x_session_id: str = Header(..., alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    try:
        await DiscussionService.check_permission(db, discussion_id, x_session_id)
        await DiscussionService.start(db, discussion_id)
    except PermissionError as e: raise HTTPException(status_code=403, detail=str(e))
    except StateConflictError as e: raise HTTPException(status_code=409, detail=str(e))
    if not runner_registry.is_running(discussion_id):
        runner = runner_registry.create_runner(discussion_id, ws_manager)
        task = asyncio.create_task(runner.run(async_session_factory))
        runner_registry.set_task(discussion_id, task)
    return ApiResponse(code=200, data={"discussion_id": discussion_id, "status": "live"}, message="讨论已开始")


# ── Pause (signal runner if exists, else write DB) ──
@router.post("/{discussion_id}/pause")
async def pause_discussion(
    discussion_id: str, x_session_id: str = Header(..., alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    try:
        await DiscussionService.check_permission(db, discussion_id, x_session_id)
    except PermissionError as e: raise HTTPException(status_code=403, detail=str(e))
    runner = runner_registry.get(discussion_id)
    if runner:
        runner.pause()
    else:
        try: await DiscussionService.pause(db, discussion_id)
        except StateConflictError as e: raise HTTPException(status_code=409, detail=str(e))
    return ApiResponse(code=200, data={"discussion_id": discussion_id, "status": "paused"}, message="讨论已暂停")


# ── Resume ──
@router.post("/{discussion_id}/resume")
async def resume_discussion(
    discussion_id: str, x_session_id: str = Header(..., alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    try:
        await DiscussionService.check_permission(db, discussion_id, x_session_id)
    except PermissionError as e: raise HTTPException(status_code=403, detail=str(e))
    runner = runner_registry.get(discussion_id)
    if runner:
        runner.resume()
    else:
        try: await DiscussionService.resume(db, discussion_id)
        except StateConflictError as e: raise HTTPException(status_code=409, detail=str(e))
    return ApiResponse(code=200, data={"discussion_id": discussion_id, "status": "live"}, message="讨论已继续")


# ── Next (launch runner if needed) ──
@router.post("/{discussion_id}/next")
async def next_round(
    discussion_id: str, x_session_id: str = Header(..., alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    try:
        await DiscussionService.check_permission(db, discussion_id, x_session_id)
        await DiscussionService.next_round(db, discussion_id)
    except PermissionError as e: raise HTTPException(status_code=403, detail=str(e))
    except StateConflictError as e: raise HTTPException(status_code=409, detail=str(e))
    runner = runner_registry.get(discussion_id)
    if not runner:
        runner = runner_registry.create_runner(discussion_id, ws_manager)
        task = asyncio.create_task(runner.run(async_session_factory))
        runner_registry.set_task(discussion_id, task)
    else:
        runner.force_step()
    return ApiResponse(code=200, data={"discussion_id": discussion_id, "round_triggered": True}, message="已触发下一轮发言")


# ── End ──
@router.post("/{discussion_id}/end")
async def end_discussion(
    discussion_id: str, x_session_id: str = Header(..., alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    try:
        await DiscussionService.check_permission(db, discussion_id, x_session_id)
    except PermissionError as e: raise HTTPException(status_code=403, detail=str(e))
    runner = runner_registry.get(discussion_id)
    if runner:
        runner.stop()   # signal runner to abort current utterance + clean up
    try:
        await DiscussionService.end(db, discussion_id)  # DB write ALWAYS
    except StateConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return ApiResponse(code=200, data={
        "discussion_id": discussion_id, "status": "ended",
        "ended_at": _now(), "total_rounds": 0, "total_utterances": 0,
    }, message="讨论已结束")


# ── Report ──
@router.get("/{discussion_id}/report")
async def get_report(discussion_id: str, db: AsyncSession = Depends(get_db)):
    report = await ReportService.generate_report(db, discussion_id)
    if report is None:
        raise HTTPException(status_code=404, detail="讨论不存在")
    return ApiResponse(code=200, data=report, message="success")
