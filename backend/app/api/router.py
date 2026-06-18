"""汇总所有 API 路由"""

from fastapi import APIRouter
from app.api.discussions import router as discussions_router
from app.api.panel import router as panel_router

router = APIRouter(prefix="/api")
router.include_router(discussions_router)
router.include_router(panel_router)
