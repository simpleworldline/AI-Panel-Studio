"""Phase 4 — llm_client.py 测试 (RED)

验证 DeepSeek API 封装: chat/chat_stream/重试/超时。
所有测试使用 httpx MockTransport，零外部 API 调用。
"""

import json
import pytest
import httpx


# ============================================================
# Helpers
# ============================================================

def _make_client(transport, base_url="https://api.deepseek.com/v1", timeout=10.0):
    from app.agents.llm_client import LLMClient
    return LLMClient(
        api_key="sk-test-key",
        base_url=base_url,
        model="deepseek-chat",
        max_retries=2,
        timeout=timeout,
        _transport=transport,
    )


def _ok_response(content: str) -> httpx.Response:
    """模拟 200 响应"""
    return httpx.Response(200, json={
        "choices": [{"message": {"content": content}}],
    })


def _stream_response(tokens: list[str]) -> httpx.Response:
    """模拟流式 SSE 响应"""
    lines = []
    for t in tokens:
        chunk = {
            "choices": [{"delta": {"content": t}}],
        }
        lines.append(f"data: {json.dumps(chunk)}\n")
    lines.append("data: [DONE]\n")
    return httpx.Response(200, text="".join(lines))


def _error_response(status: int, message: str = "Error") -> httpx.Response:
    return httpx.Response(status, json={"error": {"message": message}})


def _json_response(data: dict) -> httpx.Response:
    return httpx.Response(200, json={
        "choices": [{"message": {"content": json.dumps(data, ensure_ascii=False)}}],
    })


# ============================================================
# chat() — 普通对话
# ============================================================

class TestChat:
    """chat() 完整响应"""

    def test_returns_content(self):
        transport = httpx.MockTransport(lambda req: _ok_response("你好，我是AI助手"))
        client = _make_client(transport)
        result = client.chat_sync([{"role": "user", "content": "你好"}])
        assert result == "你好，我是AI助手"

    def test_passes_api_key_in_header(self):
        captured_headers = []

        def handler(req):
            captured_headers.append(dict(req.headers))
            return _ok_response("ok")

        client = _make_client(httpx.MockTransport(handler))
        client.chat_sync([{"role": "user", "content": "hi"}])
        assert any("authorization" in k.lower() for k in captured_headers[0])

    def test_passes_model_in_body(self):
        captured_body = {}

        def handler(req):
            nonlocal captured_body
            captured_body = json.loads(req.content)
            return _ok_response("ok")

        client = _make_client(httpx.MockTransport(handler))
        client.chat_sync([{"role": "user", "content": "hi"}])
        assert captured_body["model"] == "deepseek-chat"


# ============================================================
# chat_stream() — 流式响应
# ============================================================

class TestChatStream:
    """chat_stream 逐 token yield"""

    def test_yields_tokens_sync(self):
        transport = httpx.MockTransport(
            lambda req: _stream_response(["我", "认为", "AI", "应该"])
        )
        client = _make_client(transport)
        tokens = list(client.chat_stream_sync([{"role": "user", "content": "?"}]))
        assert tokens == ["我", "认为", "AI", "应该"]

    def test_handles_empty_stream(self):
        transport = httpx.MockTransport(lambda req: httpx.Response(200, text="data: [DONE]\n"))
        client = _make_client(transport)
        tokens = list(client.chat_stream_sync([{"role": "user", "content": "?"}]))
        assert tokens == []


# ============================================================
# chat_json() — 结构化 JSON 输出
# ============================================================

class TestChatJSON:
    """chat_json 解析 JSON 响应"""

    def test_parses_json(self):
        transport = httpx.MockTransport(
            lambda req: _json_response({"title": "共识", "confidence": 0.92})
        )
        client = _make_client(transport)
        result = client.chat_json_sync([{"role": "user", "content": "分析"}])
        assert result == {"title": "共识", "confidence": 0.92}

    def test_handles_markdown_json_block(self):
        """处理 LLM 输出 ``json ... `` 包裹的情况"""
        resp = httpx.Response(200, json={
            "choices": [{"message": {"content": '```json\n{"key": "value"}\n```'}}],
        })
        client = _make_client(httpx.MockTransport(lambda req: resp))
        result = client.chat_json_sync([{"role": "user", "content": "x"}])
        assert result == {"key": "value"}


# ============================================================
# 重试机制
# ============================================================

class TestRetry:
    """max_retries=2 — 最多 3 次尝试 (初次 + 2 次重试)"""

    def test_retries_then_succeeds(self):
        call_count = [0]

        def handler(req):
            call_count[0] += 1
            if call_count[0] < 3:
                return _error_response(500, "Server Error")
            return _ok_response("恢复了")

        client = _make_client(httpx.MockTransport(handler))
        result = client.chat_sync([{"role": "user", "content": "hi"}])
        assert result == "恢复了"
        assert call_count[0] == 3

    def test_exhausts_retries_then_raises(self):
        def handler(req):
            return _error_response(500, "Server Error")

        client = _make_client(httpx.MockTransport(handler))
        with pytest.raises(Exception) as e:
            client.chat_sync([{"role": "user", "content": "hi"}])
        assert "LLM API Error" in str(e.value) or "Server Error" in str(e.value)


class TestTimeout:
    """超时处理 — MockTransport 无法模拟超时，改为直接测试 _retry 逻辑"""

    def test_timeout_triggers_retry_then_succeeds(self):
        """_retry 遇到 TimeoutException 先重试，耗尽前成功"""
        from app.agents.llm_client import LLMClient, LLMTimeoutError
        call_count = [0]

        def fail_twice(_messages):
            call_count[0] += 1
            if call_count[0] < 3:
                raise httpx.TimeoutException("timeout")
            return "最终成功"

        client = LLMClient(api_key="sk-x", max_retries=2)
        result = client._retry(fail_twice, [{"role": "user", "content": "hi"}])
        assert result == "最终成功"
        assert call_count[0] == 3

    def test_timeout_exhausted_raises_llm_timeout(self):
        """_retry 耗尽重试后抛出 LLMTimeoutError"""
        from app.agents.llm_client import LLMClient, LLMTimeoutError

        def always_timeout(_messages):
            raise httpx.TimeoutException("timeout")

        client = LLMClient(api_key="sk-x", max_retries=2)
        with pytest.raises(LLMTimeoutError):
            client._retry(always_timeout, [{"role": "user", "content": "hi"}])
