"""讨论 API 路由 — 对齐 API_CONTRACT.md §2"""

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.discussion import DiscussionCreate
from app.schemas.common import ApiResponse
from app.services.discussion_service import DiscussionService, StatusError

router = APIRouter(prefix="/discussions", tags=["discussions"])


def _session_id(request: Request) -> str:
    return request.headers.get("X-Session-Id", "anonymous")


def _service(request: Request, session: AsyncSession) -> DiscussionService:
    return DiscussionService(session, _session_id(request))


@router.post("", status_code=201)
async def create_discussion(
    request: Request, data: DiscussionCreate,
    session: AsyncSession = Depends(get_db),
):
    svc = _service(request, session)
    try:
        d = await svc.create(data)
        return ApiResponse(code=201, data=DiscussionService._dict(d), message="讨论创建成功")
    except StatusError as e:
        return ApiResponse(code=e.code, data=None, message=e.message, detail=str(e.code))


@router.get("")
async def list_discussions(
    request: Request,
    status: str | None = Query(None), page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    session: AsyncSession = Depends(get_db),
):
    svc = _service(request, session)
    items, total = await svc.list_all(status=status, page=page, page_size=page_size)
    return ApiResponse(code=200, data={"items": items, "total": total, "page": page, "page_size": page_size}, message="success")


@router.get("/{discussion_id}")
async def get_discussion(
    discussion_id: str, request: Request,
    session: AsyncSession = Depends(get_db),
):
    svc = _service(request, session)
    try:
        detail = await svc.get_detail(discussion_id)
        from app.services.discussion_manager import get_runner
        runner = get_runner(discussion_id)
        if runner and runner.transcript:
            detail["transcript"] = runner.transcript
            detail["current_round"] = runner.current_round
            detail["consensus"] = runner.consensus_items
            detail["disagreements"] = runner.disagreement_items
            detail["status"] = runner._status
        return ApiResponse(code=200, data=detail, message="success")
    except StatusError as e:
        return ApiResponse(code=e.code, data=None, message=e.message, detail=str(e.code))


@router.post("/{discussion_id}/start")
async def start_discussion(
    discussion_id: str, request: Request,
    session: AsyncSession = Depends(get_db),
):
    svc = _service(request, session)
    try:
        d = await svc.start(discussion_id)
        detail = await svc.get_detail(discussion_id)
        panel = detail.get("panel", [])
        from app.services.discussion_manager import start_discussion_runner
        await start_discussion_runner(discussion_id, d.topic, panel, max_rounds=d.max_rounds)
        return ApiResponse(code=200, data={"discussion_id": d.id, "status": d.status}, message="讨论已开始")
    except StatusError as e:
        return ApiResponse(code=e.code, data=None, message=e.message, detail=str(e.code))


@router.post("/{discussion_id}/pause")
async def pause_discussion(
    discussion_id: str, request: Request,
    session: AsyncSession = Depends(get_db),
):
    svc = _service(request, session)
    try:
        d = await svc.pause(discussion_id)
        # 同时通知 runner
        from app.services.discussion_manager import get_runner
        runner = get_runner(discussion_id)
        if runner:
            await runner.pause()
        return ApiResponse(code=200, data={"discussion_id": d.id, "status": d.status}, message="讨论已暂停")
    except StatusError as e:
        return ApiResponse(code=e.code, data=None, message=e.message, detail=str(e.code))


@router.post("/{discussion_id}/resume")
async def resume_discussion(
    discussion_id: str, request: Request,
    session: AsyncSession = Depends(get_db),
):
    svc = _service(request, session)
    try:
        d = await svc.resume(discussion_id)
        from app.services.discussion_manager import get_runner
        runner = get_runner(discussion_id)
        if runner:
            await runner.resume()
        return ApiResponse(code=200, data={"discussion_id": d.id, "status": d.status}, message="讨论已继续")
    except StatusError as e:
        return ApiResponse(code=e.code, data=None, message=e.message, detail=str(e.code))


@router.post("/{discussion_id}/next")
async def advance_discussion(
    discussion_id: str, request: Request,
    session: AsyncSession = Depends(get_db),
):
    from app.services.discussion_manager import get_runner
    runner = get_runner(discussion_id)
    if runner:
        await runner._run_one_round()
    return ApiResponse(code=200, data={"discussion_id": discussion_id, "round_triggered": True}, message="已触发下一轮发言")


@router.post("/{discussion_id}/end")
async def end_discussion(
    discussion_id: str, request: Request,
    session: AsyncSession = Depends(get_db),
):
    svc = _service(request, session)
    try:
        d = await svc.end(discussion_id)
        from app.services.discussion_manager import get_runner
        runner = get_runner(discussion_id)
        if runner:
            await runner.force_end()
        return ApiResponse(code=200, data={
            "discussion_id": d.id, "status": d.status,
            "ended_at": d.ended_at, "total_rounds": d.current_round,
            "total_utterances": 0,
        }, message="讨论已结束")
    except StatusError as e:
        return ApiResponse(code=e.code, data=None, message=e.message, detail=str(e.code))


@router.get("/{discussion_id}/report")
async def get_report(
    discussion_id: str, request: Request,
    session: AsyncSession = Depends(get_db),
):
    svc = _service(request, session)
    try:
        detail = await svc.get_detail(discussion_id)
        transcript = detail["transcript"]
        host_summary = ""
        for u in transcript[::-1]:
            if u.get("utterance_type") == "summary":
                host_summary = u["content"]
                break
        return ApiResponse(code=200, data={
            "discussion_id": discussion_id, "topic": detail["topic"],
            "panel": detail["panel"], "transcript": transcript,
            "consensus": detail["consensus"], "disagreements": detail["disagreements"],
            "host_summary": host_summary,
        }, message="success")
    except StatusError as e:
        return ApiResponse(code=e.code, data=None, message=e.message, detail=str(e.code))
