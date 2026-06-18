"""AI Panel Studio — FastAPI 依赖注入 get_db"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖 — 每次请求获取独立 session，请求结束自动关闭"""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
