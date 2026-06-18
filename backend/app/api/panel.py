"""嘉宾 API 路由 — 对齐 API_CONTRACT.md §2.2"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.panel import PanelGenerateRequest, PanelConfirmRequest
from app.schemas.common import ApiResponse
from app.services.panel_service import PanelService
from app.services.discussion_service import StatusError

router = APIRouter()


def _svc(request: Request, session: AsyncSession, llm=None):
    return PanelService(session, llm, request.headers.get("X-Session-Id", "anonymous"))


@router.post("/discussions/{discussion_id}/panel/generate")
async def generate_panel(
    discussion_id: str,
    data: PanelGenerateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    from app.agents.llm_client import LLMClient
    from app.config import settings
    try:
        llm = _build_llm()
    except Exception:
        llm = None
    svc = PanelService(session, llm, request.headers.get("X-Session-Id", "anonymous"))
    try:
        result = await svc.generate(discussion_id, data.regenerate_member_id)
        return ApiResponse(code=200, data=result, message="嘉宾阵容生成成功")
    except StatusError as e:
        return ApiResponse(code=e.code, data=None, message=e.message, detail=str(e.code))


@router.put("/discussions/{discussion_id}/panel")
async def confirm_panel(
    discussion_id: str,
    data: PanelConfirmRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    from app.agents.llm_client import LLMClient
    try:
        llm = _build_llm()
    except Exception:
        llm = None
    svc = PanelService(session, llm, request.headers.get("X-Session-Id", "anonymous"))
    try:
        members = await svc.confirm(discussion_id, data)
        return ApiResponse(
            code=200,
            data={"discussion_id": discussion_id, "panel_confirmed": True, "members": members},
            message="嘉宾阵容确认成功",
        )
    except StatusError as e:
        return ApiResponse(code=e.code, data=None, message=e.message, detail=str(e.code))


def _build_llm():
    from app.config import settings
    from app.agents.llm_client import LLMClient
    return LLMClient(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.deepseek_model,
        max_retries=settings.llm_max_retries,
    )
