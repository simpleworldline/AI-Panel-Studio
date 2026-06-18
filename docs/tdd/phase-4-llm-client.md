# Phase 4 — llm_client.py 测试报告

> **阶段**: TDD  
> **日期**: 2026-06-18  
> **状态**: ✅ PASSED (11/11 新增, 72/72 累计)

---

## 1. TDD 执行记录

| 步 | 动作 | 结果 |
|----|------|------|
| 🔴 | 写 `test_llm_client.py` (10 tests) | 10 FAILED — ModuleNotFoundError |
| 🟢 | 写 `app/agents/llm_client.py` (180 行) | 9 PASSED, 1 fail — timeout test 用 MockTransport 无效 |
| 🟡 | 修复 timeout 测试 + _retry TimeoutException→LLMTimeoutError | 11 PASSED |
| 🔵 | Refactor | 无需 |

---

## 2. 测试清单

| 场景 | 测试 | 验证 |
|------|------|------|
| **chat()** | `test_returns_content` | 同步返回 LLM 文本 |
| | `test_passes_api_key_in_header` | `Authorization: Bearer sk-...` |
| | `test_passes_model_in_body` | `model: deepseek-chat` |
| **chat_stream()** | `test_yields_tokens_sync` | 逐 token yield |
| | `test_handles_empty_stream` | 空流处理 |
| **chat_json()** | `test_parses_json` | JSON.parse 响应 |
| | `test_handles_markdown_json_block` | 剥离 ```json``` 包装 |
| **重试** | `test_retries_then_succeeds` | 2 次重试后成功 (共 3 次调用) |
| | `test_exhausts_retries_then_raises` | 耗尽后抛出 LLMAPIError |
| **超时** | `test_timeout_triggers_retry_then_succeeds` | TimeoutException 重试→成功 |
| | `test_timeout_exhausted_raises_llm_timeout` | 耗尽后抛出 LLMTimeoutError |

---

## 3. DeepSeek API 对齐

| API 要求 | 实现 |
|----------|------|
| Base URL | `https://api.deepseek.com/v1` |
| Endpoint | `/chat/completions` |
| Auth | `Authorization: Bearer {api_key}` |
| Request body | `{model, messages}` |
| Stream | `stream: true` → SSE `data: {...}` |
| 响应格式 | `choices[0].message.content` |

---

## 4. 回归验证

```
tests/unit/: 72 passed in 4.26s
  test_config.py ............ 8 passed
  test_database.py ........... 6 passed
  test_infrastructure.py .... 13 passed
  test_models.py ............ 22 passed
  test_scheduler.py ......... 12 passed
  test_llm_client.py ........ 11 passed  ← 新增
```

---

## 5. 环境配置

```bash
# backend/.env (已创建, 已加入 .gitignore)
DEEPSEEK_API_KEY=XXX
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
```
