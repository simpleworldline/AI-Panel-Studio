"""Phase 0 — 测试基础设施验证

确保 MockLLMClient、async engine、factories 正常工作，
为后续 TDD 阶段提供可信基础。
"""

import asyncio
import pytest
from sqlalchemy import text


def _run(coro):
    """在同步测试中运行 async 方法"""
    return asyncio.run(coro)


# ============================================================
# MockLLMClient 验证
# ============================================================

class TestMockLLMClientChat:
    """chat() 方法验证"""

    def test_returns_preset_response(self, mock_llm_client):
        mock_llm_client.set_chat_response("你好，我是AI助手")
        result = _run(mock_llm_client.chat([{"role": "user", "content": "你好"}]))
        assert result == "你好，我是AI助手"

    def test_raises_after_configured_failures(self, mock_llm_client):
        mock_llm_client.set_fail(count=2, message="API Error")
        # 第一次失败
        with pytest.raises(Exception) as e1:
            _run(mock_llm_client.chat([{"role": "user", "content": "hi"}]))
        assert "API Error" in str(e1.value)
        # 第二次失败
        with pytest.raises(Exception):
            _run(mock_llm_client.chat([{"role": "user", "content": "hi"}]))
        # 第三次成功
        mock_llm_client.set_chat_response("恢复了")
        result = _run(mock_llm_client.chat([{"role": "user", "content": "hi"}]))
        assert result == "恢复了"

    def test_records_call_history(self, mock_llm_client):
        mock_llm_client.set_chat_response("ok")
        _run(mock_llm_client.chat([{"role": "system", "content": "你是专家"}]))
        assert len(mock_llm_client._call_history) == 1
        assert mock_llm_client._call_history[0]["method"] == "chat"


class TestMockLLMClientStream:
    """chat_stream() 方法验证"""

    async def test_yields_tokens_in_order(self, mock_llm_client):
        mock_llm_client.set_stream_tokens(["我", "认为", "AI", "应该"])
        tokens = []
        async for t in mock_llm_client.chat_stream([{"role": "user", "content": "?"}]):
            tokens.append(t)
        assert tokens == ["我", "认为", "AI", "应该"]

    async def test_raises_on_configured_failure(self, mock_llm_client):
        mock_llm_client.set_fail(count=1)
        with pytest.raises(Exception):
            async for _ in mock_llm_client.chat_stream([{"role": "user", "content": "?"}]):
                pass


class TestMockLLMClientJSON:
    """chat_json() 方法验证"""

    def test_returns_preset_json(self, mock_llm_client):
        mock_llm_client.set_json_response({"title": "共识", "confidence": 0.92})
        result = _run(mock_llm_client.chat_json([{"role": "user", "content": "分析"}]))
        assert result == {"title": "共识", "confidence": 0.92}


# ============================================================
# Async Engine 验证
# ============================================================

class TestAsyncEngine:
    """数据库引擎和 Session 验证"""

    async def test_engine_creates_successfully(self, async_engine):
        assert async_engine is not None

    async def test_session_factory_yields_session(self, async_session_factory):
        async with async_session_factory() as session:
            assert session is not None
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

    async def test_foreign_keys_enabled(self, async_engine):
        async with async_engine.connect() as conn:
            result = await conn.execute(text("PRAGMA foreign_keys"))
            row = result.fetchone()
            assert row[0] == 1


# ============================================================
# Factories 验证
# ============================================================

class TestDiscussionFactory:
    """Discussion 数据工厂"""

    def test_default_values(self):
        from tests.factories.discussion_factory import make_discussion_row
        row = make_discussion_row()
        assert row["status"] == "pending"
        assert row["expert_count"] == 4
        assert row["current_round"] == 0
        assert row["max_rounds"] is None
        assert row["rounds_without_consensus"] == 0
        assert "id" in row

    def test_custom_values(self):
        from tests.factories.discussion_factory import make_discussion_row
        row = make_discussion_row(topic="量子计算", status="live", current_round=5)
        assert row["topic"] == "量子计算"
        assert row["status"] == "live"
        assert row["current_round"] == 5


class TestPanelMemberFactory:
    """PanelMember 数据工厂"""

    def test_make_host(self):
        from tests.factories.panel_member_factory import make_host_row
        host = make_host_row(discussion_id="d1", name="周教授")
        assert host["role"] == "host"
        assert host["sort_order"] == 0
        assert host["name"] == "周教授"

    def test_make_experts(self):
        from tests.factories.panel_member_factory import make_expert_rows
        experts = make_expert_rows(discussion_id="d1", count=3)
        assert len(experts) == 3
        for e in experts:
            assert e["role"] == "expert"
            assert e["discussion_id"] == "d1"
        assert experts[0]["sort_order"] == 1
        assert experts[1]["sort_order"] == 2
        assert experts[2]["sort_order"] == 3
