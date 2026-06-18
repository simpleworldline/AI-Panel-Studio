"""Pytest 全局 Fixtures — Phase 0 基础设施

提供:
- async_engine: SQLite 内存数据库引擎
- async_session_factory: 异步 Session 工厂
- db_session: 每个测试独立的 async session
- mock_llm_client: 预设响应的 LLM Client (零外部 API 调用)
"""

import uuid
import pytest
from sqlalchemy import text, event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


# ============================================================
# Database Fixture — 每个测试独立的内存 SQLite
# ============================================================

@pytest.fixture
async def async_engine():
    """异步 SQLite 内存引擎 (WAL 模式)"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # 设置 SQLite PRAGMA (通过同步事件)
    @event.listens_for(engine.sync_engine, "connect")
    def _set_pragma(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # 确保至少一次连接来触发事件
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))

    yield engine
    await engine.dispose()


@pytest.fixture
async def async_session_factory(async_engine):
    """异步 Session 工厂"""
    return async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db_session(async_session_factory):
    """每个测试独立的 async session (自动 rollback)"""
    async with async_session_factory() as session:
        yield session
        await session.rollback()


# ============================================================
# Mock LLM Client — 零外部 API 调用的可编程 Agent 后端
# ============================================================

class MockLLMClient:
    """可编程 Mock，用于 Agent 单元测试。

    使用方法:
        mock.set_chat_response("你好，世界")
        mock.set_stream_tokens(["我", "认为", "..."])
        mock.set_json_response({"title": "共识", "confidence": 0.9})
    """

    def __init__(self):
        self._chat_response: str = ""
        self._stream_tokens: list[str] = []
        self._json_response: dict | None = None
        self._should_fail_count: int = 0
        self._fail_message: str = "LLM API Error"
        self._call_history: list[dict] = []

    # ── 配置方法 ──

    def set_chat_response(self, text: str):
        self._chat_response = text

    def set_stream_tokens(self, tokens: list[str]):
        self._stream_tokens = tokens

    def set_json_response(self, data: dict):
        self._json_response = data

    def set_fail(self, count: int = 1, message: str = "LLM API Error"):
        """前 count 次调用返回失败"""
        self._should_fail_count = count
        self._fail_message = message

    # ── 调用方法 (兼容真实 LLM Client 接口) ──

    async def chat(self, messages: list[dict], **kwargs) -> str:
        self._call_history.append({"method": "chat", "messages": messages, "kwargs": kwargs})
        if self._should_fail_count > 0:
            self._should_fail_count -= 1
            raise LLMAPIError(self._fail_message)
        return self._chat_response

    async def chat_stream(self, messages: list[dict], **kwargs):
        """异步生成器 — 逐 token yield"""
        self._call_history.append({"method": "chat_stream", "messages": messages, "kwargs": kwargs})
        if self._should_fail_count > 0:
            self._should_fail_count -= 1
            raise LLMAPIError(self._fail_message)
        for token in self._stream_tokens:
            yield token

    async def chat_json(self, messages: list[dict], **kwargs) -> dict:
        self._call_history.append({"method": "chat_json", "messages": messages, "kwargs": kwargs})
        if self._should_fail_count > 0:
            self._should_fail_count -= 1
            raise LLMAPIError(self._fail_message)
        return self._json_response or {}


class LLMAPIError(Exception):
    """LLM API 调用异常"""
    pass


class LLMTimeoutError(Exception):
    """LLM API 超时"""
    pass


@pytest.fixture
def mock_llm_client():
    """每个测试独立的 Mock LLM Client"""
    return MockLLMClient()


# ============================================================
# UUID Generator Helper
# ============================================================

@pytest.fixture
def gen_uuid():
    return lambda: str(uuid.uuid4())
