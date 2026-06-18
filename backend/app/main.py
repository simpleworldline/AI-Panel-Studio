"""FastAPI 应用入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router as api_router
from app.api.ws import router as ws_router
from app.models import Base
from app.db.session import _get_factory


def create_app() -> FastAPI:
    app = FastAPI(title="AI Panel Studio API", version="1.0.0")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    app.include_router(ws_router)

    @app.on_event("startup")
    async def startup():
        # 初始化数据库表
        factory = _get_factory()
        async with factory() as session:
            async with session.bind.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

    @app.get("/api/health")
    async def health():
        return {"code": 200, "data": {"status": "ok"}, "message": "success"}

    return app


app = create_app()
