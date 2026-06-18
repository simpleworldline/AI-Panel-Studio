"""pytest fixtures — 使用 SQLite in-memory 数据库进行测试"""

import asyncio
import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_engine():
    """In-memory SQLite engine — 每次测试独立建表/删表"""
    from app.db.database import Base

    engine = create_async_engine("sqlite+aiosqlite://", echo=False, connect_args={"check_same_thread": False})

    # 为测试引擎启用 WAL 模式 + 外键约束
    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def _session_factory(async_engine):
    """Session factory — 每次请求创建新 session，请求结束自动 commit（匹配生产行为）"""
    factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    return factory


@pytest.fixture
async def async_session(_session_factory):
    """直接 DB 测试用的 session — 测试内部可手动 flush/rollback"""
    async with _session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def creator_headers():
    """测试用的创建者 Session ID"""
    return {"X-Session-Id": "test-session-creator"}


@pytest.fixture
async def client(_session_factory):
    """HTTPX async test client — 每次请求独立 session，匹配生产 get_db 行为"""
    from app.main import app
    from app.db.session import get_db
    from httpx import ASGITransport, AsyncClient

    async def override_get_db():
        """模拟生产 get_db：独立 session + commit + close"""
        async with _session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
