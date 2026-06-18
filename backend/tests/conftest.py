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
async def async_session(async_engine):
    """Async session — 每次测试独立 session，测试结束自动 rollback"""
    factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def creator_headers():
    """测试用的创建者 Session ID"""
    return {"X-Session-Id": "test-session-creator"}


@pytest.fixture
async def client(async_session):
    """HTTPX async test client with dependency override"""
    from app.main import app
    from app.db.session import get_db
    from httpx import ASGITransport, AsyncClient

    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
