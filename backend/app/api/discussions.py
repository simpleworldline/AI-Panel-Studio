"""API_CONTRACT.md §2.1, §2.3 — Discussion management endpoints"""

import asyncio

from fastapi import APIRouter, Depends, Header, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.database import async_session_factory
from app.schemas.discussion import DiscussionCreate
from app.schemas.common import ApiResponse
from app.services.discussion_service import DiscussionService, PermissionError, StateConflictError
from app.services.report_service import ReportService
from app.services.runner_registry import runner_registry
from app.api.ws import manager as ws_manager

router = APIRouter(prefix="/api/discussions", tags=["discussions"])


@router.post("", status_code=201)
async def create_discussion(
    body: DiscussionCreate,
    x_session_id: str = Header(..., alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    d = await DiscussionService.create(
        db, topic=body.topic, creator_session_id=x_session_id,
        expert_count=body.expert_count, max_rounds=body.max_rounds,
    )
    return ApiResponse(
        code=201,
        data={
            "id": d.id, "topic": d.topic, "expert_count": d.expert_count,
            "max_rounds": d.max_rounds, "status": d.status,
            "creator_session_id": d.creator_session_id,
            "current_round": d.current_round, "created_at": d.created_at,
        },
        message="讨论创建成功",
    )


@router.get("")
async def list_discussions(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await DiscussionService.list_discussions(db, status=status, page=page, page_size=page_size)
    return ApiResponse(code=200, data=result, message="success")


@router.get("/{discussion_id}")
async def get_discussion(
    discussion_id: str,
    db: AsyncSession = Depends(get_db),
):
    detail = await DiscussionService.get_detail(db, discussion_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="讨论不存在")
    return ApiResponse(code=200, data=detail, message="success")


@router.post("/{discussion_id}/start")
async def start_discussion(
    discussion_id: str,
    x_session_id: str = Header(..., alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    try:
        await DiscussionService.check_permission(db, discussion_id, x_session_id)
        result = await DiscussionService.start(db, discussion_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Launch DiscussionRunner as background task
    if not runner_registry.is_running(discussion_id):
        runner = runner_registry.create_runner(discussion_id, ws_manager)
        asyncio.create_task(runner.run(async_session_factory))

    return ApiResponse(code=200, data=result, message="讨论已开始")


@router.post("/{discussion_id}/pause")
async def pause_discussion(
    discussion_id: str,
    x_session_id: str = Header(..., alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    try:
        await DiscussionService.check_permission(db, discussion_id, x_session_id)
        result = await DiscussionService.pause(db, discussion_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Signal runner to pause
    runner = runner_registry.get(discussion_id)
    if runner:
        asyncio.create_task(runner.pause())

    return ApiResponse(code=200, data=result, message="讨论已暂停")


@router.post("/{discussion_id}/resume")
async def resume_discussion(
    discussion_id: str,
    x_session_id: str = Header(..., alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    try:
        await DiscussionService.check_permission(db, discussion_id, x_session_id)
        result = await DiscussionService.resume(db, discussion_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Signal runner to resume
    runner = runner_registry.get(discussion_id)
    if runner:
        asyncio.create_task(runner.resume())

    return ApiResponse(code=200, data=result, message="讨论已继续")


@router.post("/{discussion_id}/next")
async def next_round(
    discussion_id: str,
    x_session_id: str = Header(..., alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    try:
        await DiscussionService.check_permission(db, discussion_id, x_session_id)
        result = await DiscussionService.next_round(db, discussion_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Force advance: briefly pause then resume to trigger one loop iteration
    runner = runner_registry.get(discussion_id)
    if runner:
        asyncio.create_task(runner.resume())

    return ApiResponse(code=200, data=result, message="已触发下一轮发言")


@router.post("/{discussion_id}/end")
async def end_discussion(
    discussion_id: str,
    x_session_id: str = Header(..., alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    try:
        await DiscussionService.check_permission(db, discussion_id, x_session_id)
        result = await DiscussionService.end(db, discussion_id)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Stop runner
    runner = runner_registry.get(discussion_id)
    if runner:
        await runner.stop()

    return ApiResponse(code=200, data=result, message="讨论已结束")


@router.get("/{discussion_id}/report")
async def get_report(
    discussion_id: str,
    db: AsyncSession = Depends(get_db),
):
    report = await ReportService.generate_report(db, discussion_id)
    if report is None:
        raise HTTPException(status_code=404, detail="讨论不存在")
    return ApiResponse(code=200, data=report, message="success")
