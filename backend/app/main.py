"""AI Panel Studio — FastAPI 应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.discussions import router as discussions_router
from app.api.panel import router as panel_router
from app.api.ws import router as ws_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 — 启动时自动建表"""
    from app.db.database import Base, engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="AI Panel Studio",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(discussions_router)
app.include_router(panel_router)
app.include_router(ws_router)


# ---- Error Handlers ----
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "code": 422,
            "data": None,
            "message": "请求参数校验失败",
        },
    )


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"code": 200, "data": {"status": "ok"}, "message": "success"}
