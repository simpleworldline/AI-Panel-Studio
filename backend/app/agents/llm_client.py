"""DeepSeek API 客户端 — 严格遵循 BACKEND_STRUCTURE.md §2.3

支持: chat / chat_stream / chat_json
重试: 最多 retry 次 (默认 2 次, 共 3 次尝试)
"""

import json
import time
import re
import httpx


class LLMAPIError(Exception):
    """LLM API 调用异常"""


class LLMTimeoutError(Exception):
    """LLM API 超时"""


class LLMClient:
    """DeepSeek API 客户端

    通过 _transport 参数注入 httpx.MockTransport 用于测试。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat",
        max_retries: int = 2,
        timeout: float = 30.0,
        _transport: httpx.BaseTransport | None = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_retries = max_retries
        self._transport = _transport
        self._timeout = httpx.Timeout(timeout)

    @property
    def _client(self) -> httpx.Client:
        return httpx.Client(
            transport=self._transport,
            timeout=self._timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

    # ================================================================
    # 同步接口 (测试用)
    # ================================================================

    def chat_sync(self, messages: list[dict]) -> str:
        """同步 chat — 带重试"""
        return self._retry(self._chat_sync_once, messages)

    def chat_stream_sync(self, messages: list[dict]):
        """同步 stream — 带重试"""
        return self._retry(self._chat_stream_sync_once, messages, retryable=False)

    def chat_json_sync(self, messages: list[dict]) -> dict:
        """同步 JSON 输出"""
        return self._retry(self._chat_json_sync_once, messages)

    # ================================================================
    # 异步接口 (生产用)
    # ================================================================

    async def chat(self, messages: list[dict]) -> str:
        async with httpx.AsyncClient(
            transport=self._transport, timeout=self._timeout,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        ) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        json={"model": self.model, "messages": messages},
                    )
                    if resp.status_code >= 400:
                        if attempt < self.max_retries:
                            continue
                        raise LLMAPIError(f"LLM API Error: {resp.status_code} {resp.text}")
                    return resp.json()["choices"][0]["message"]["content"]
                except httpx.TimeoutException:
                    if attempt < self.max_retries:
                        continue
                    raise LLMTimeoutError("LLM API 超时")
            raise LLMAPIError("LLM API Error: max retries exceeded")

    async def chat_stream(self, messages: list[dict]):
        """异步流式生成 — 直接用 aiter_bytes 手动解析 SSE"""
        stream_timeout = httpx.Timeout(connect=10.0, read=90.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(
            transport=self._transport, timeout=stream_timeout,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        ) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json={"model": self.model, "messages": messages, "stream": True},
            ) as resp:
                if resp.status_code >= 400:
                    await resp.aread()
                    raise LLMAPIError(f"LLM API Error: {resp.status_code}")
                buffer = ""
                async for chunk in resp.aiter_bytes():
                    buffer += chunk.decode("utf-8", errors="replace")
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line or not line.startswith("data:"):
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:]
                        else:
                            data_str = line[5:]
                        if data_str == "[DONE]":
                            return
                        try:
                            token = json.loads(data_str)["choices"][0]["delta"].get("content", "")
                            if token:
                                yield token
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

    async def chat_json(self, messages: list[dict]) -> dict:
        text = await self.chat(messages)
        return self._extract_json(text)

    # ================================================================
    # 内部
    # ================================================================

    def _chat_sync_once(self, messages: list[dict]) -> str:
        with self._client as client:
            resp = client.post(
                f"{self.base_url}/chat/completions",
                json={"model": self.model, "messages": messages},
            )
            if resp.status_code >= 400:
                raise LLMAPIError(f"LLM API Error: {resp.status_code} {resp.text}")
            return resp.json()["choices"][0]["message"]["content"]

    def _chat_stream_sync_once(self, messages: list[dict]):
        with self._client as client:
            with client.stream("POST", f"{self.base_url}/chat/completions",
                               json={"model": self.model, "messages": messages, "stream": True}) as resp:
                if resp.status_code >= 400:
                    raise LLMAPIError(f"LLM API Error: {resp.status_code} {resp.text}")
                for line in resp.iter_lines():
                    line = line.strip()
                    if not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        token = chunk["choices"][0]["delta"].get("content", "")
                        if token:
                            yield token
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    def _chat_json_sync_once(self, messages: list[dict]) -> dict:
        text = self._chat_sync_once(messages)
        return self._extract_json(text)

    def _retry(self, fn, *args, retryable: bool = True):
        """重试循环"""
        last_err = None
        for attempt in range(self.max_retries + 1):
            try:
                return fn(*args)
            except httpx.TimeoutException as e:
                last_err = e
                if not retryable or attempt >= self.max_retries:
                    raise LLMTimeoutError("LLM API 超时") from e
                time.sleep(0.3 * (2 ** attempt))
            except LLMAPIError as e:
                last_err = e
                if not retryable or attempt >= self.max_retries:
                    raise
                time.sleep(0.3 * (2 ** attempt))
        raise LLMAPIError("LLM API Error: max retries exceeded")

    @staticmethod
    def _extract_json(text: str) -> dict:
        """从 LLM 输出中提取 JSON，处理 markdown 代码块"""
        text = text.strip()
        m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if m:
            text = m.group(1)
        return json.loads(text)
