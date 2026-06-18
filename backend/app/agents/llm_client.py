"""LLM Client — DeepSeek API 封装，支持流式 + 重试"""

import asyncio
from typing import AsyncGenerator

import httpx

from app.config import settings


class LLMClient:
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.base_url = settings.deepseek_base_url.rstrip("/")
        self.model = settings.deepseek_model
        self.max_retries = settings.llm_max_retries

    async def _request(
        self,
        messages: list[dict],
        stream: bool = False,
        temperature: float = 1.0,
        max_tokens: int = 1024,
    ) -> dict | None:
        """发送请求（带重试）"""
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model,
                            "messages": messages,
                            "stream": stream,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        },
                    )
                    if resp.status_code != 200:
                        if attempt < self.max_retries:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        return None
                    return resp.json()
            except Exception:
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
        return None

    async def chat(self, messages: list[dict], temperature: float = 1.0, max_tokens: int = 1024) -> str:
        """非流式调用 → 返回完整回复文本"""
        result = await self._request(messages, stream=False, temperature=temperature, max_tokens=max_tokens)
        if result is None:
            return ""
        choices = result.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "")

    async def chat_stream(self, messages: list[dict], temperature: float = 1.0, max_tokens: int = 1024) -> AsyncGenerator[str, None]:
        """流式调用 → 逐 token yield"""
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream(
                        "POST",
                        f"{self.base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.model,
                            "messages": messages,
                            "stream": True,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        },
                    ) as resp:
                        if resp.status_code != 200:
                            if attempt < self.max_retries:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            return
                        async for line in resp.aiter_lines():
                            if line.startswith("data:"):
                                data = line[5:].strip()
                                if data == "[DONE]":
                                    return
                                try:
                                    chunk = __import__("json").loads(data)
                                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                                    content = delta.get("content", "")
                                    if content:
                                        yield content
                                except (json.JSONDecodeError, KeyError, IndexError):
                                    continue
                return  # success, don't retry
            except Exception:
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return

    def create_messages(self, system_prompt: str, user_message: str) -> list[dict]:
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]


# 全局单例
import json  # noqa: E402

llm_client = LLMClient()
