"""API_CONTRACT.md §2.2 — 嘉宾阵容端点"""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.panel import PanelGenerateRequest, PanelConfirmRequest
from app.services.panel_service import PanelService

router = APIRouter(prefix="/api/discussions/{discussion_id}/panel", tags=["panel"])


@router.post("/generate")
async def generate_panel(
    discussion_id: str,
    body: PanelGenerateRequest = PanelGenerateRequest(),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await PanelService.generate_panel(
            db, discussion_id,
            regenerate_member_id=body.regenerate_member_id,
        )
        return ApiResponse(code=200, data=result, message="嘉宾阵容生成成功")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("")
async def confirm_panel(
    discussion_id: str,
    body: PanelConfirmRequest,
    x_session_id: str = Header(..., alias="X-Session-Id"),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await PanelService.confirm_panel(
            db, discussion_id,
            host=body.host.model_dump(),
            experts=[e.model_dump() for e in body.experts],
        )
        return ApiResponse(code=200, data=result, message="嘉宾阵容确认成功")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
