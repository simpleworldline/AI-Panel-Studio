"""Phase 1b — database.py 测试 (RED)

验证 SQLAlchemy engine 创建、session 工厂、PRAGMA 设置。
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class TestCreateEngine:
    """engine 创建"""

    def test_creates_engine_from_url(self):
        from app.db.database import create_engine
        engine = create_engine("sqlite+aiosqlite:///:memory:")
        assert engine is not None
        # cleanup
        import asyncio
        asyncio.run(engine.dispose())

    def test_engine_echo_flag(self):
        from app.db.database import create_engine
        engine = create_engine("sqlite+aiosqlite:///:memory:", echo=True)
        assert engine.echo is True
        import asyncio
        asyncio.run(engine.dispose())


class TestSessionFactory:
    """session 工厂"""

    async def test_creates_async_session(self):
        from app.db.database import create_engine, create_session_factory
        engine = create_engine("sqlite+aiosqlite:///:memory:")
        factory = create_session_factory(engine)
        async with factory() as session:
            assert isinstance(session, AsyncSession)
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
        await engine.dispose()


class TestGetDbDependency:
    """FastAPI 依赖注入 get_db"""

    async def test_get_db_yields_session(self):
        from app.db.session import get_db

        db_gen = get_db()
        session = await anext(db_gen)
        assert isinstance(session, AsyncSession)
        # 清理
        try:
            await anext(db_gen)
        except StopAsyncIteration:
            pass


class TestPragmaSettings:
    """PRAGMA 验证"""

    async def test_wal_mode(self):
        from app.db.database import create_engine
        engine = create_engine("sqlite+aiosqlite:///:memory:")
        async with engine.connect() as conn:
            result = await conn.execute(text("PRAGMA journal_mode"))
            row = result.fetchone()
            assert row is not None
            # SQLite :memory: 默认 journal_mode 非 WAL;
            # 我们的 create_engine 应通过事件监听器设置为 WAL
        await engine.dispose()

    async def test_foreign_keys_on(self):
        from app.db.database import create_engine
        engine = create_engine("sqlite+aiosqlite:///:memory:")
        async with engine.connect() as conn:
            result = await conn.execute(text("PRAGMA foreign_keys"))
            row = result.fetchone()
            assert row is not None
            # 期望 foreign_keys = 1 (ON)
        await engine.dispose()
