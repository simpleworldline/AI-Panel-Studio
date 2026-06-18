# Phase 0 — 测试基础设施报告

> **阶段**: TDD  
> **日期**: 2026-06-18  
> **状态**: ✅ PASSED (13/13)

---

## 1. 交付物

| 文件 | 描述 | 行数 |
|------|------|------|
| `tests/__init__.py` | 测试包入口 | 0 |
| `tests/conftest.py` | 全局 fixtures — async engine / mock LLM / factories | 123 |
| `tests/factories/__init__.py` | 工厂包入口 | 0 |
| `tests/factories/discussion_factory.py` | Discussion 测试数据工厂 | 25 |
| `tests/factories/panel_member_factory.py` | PanelMember 测试数据工厂 | 47 |
| `tests/unit/__init__.py` | 单元测试包 | 0 |
| `tests/unit/test_infrastructure.py` | 基础设施验证测试 | 84 |
| `tests/integration/__init__.py` | 集成测试包 | 0 |
| `tests/e2e/__init__.py` | E2E 测试包 | 0 |

---

## 2. 测试结果

```
tests/unit/test_infrastructure.py: 13 passed in 0.16s
```

| # | 测试 | 结果 |
|---|------|------|
| 1 | MockLLMClient.chat() 返回预设响应 | ✅ |
| 2 | MockLLMClient.chat() 配置失败次数后抛异常 | ✅ |
| 3 | MockLLMClient.chat() 记录调用历史 | ✅ |
| 4 | MockLLMClient.chat_stream() 按序 yield token | ✅ |
| 5 | MockLLMClient.chat_stream() 失败抛异常 | ✅ |
| 6 | MockLLMClient.chat_json() 返回预设 JSON | ✅ |
| 7 | async_engine 创建成功 | ✅ |
| 8 | async_session 可执行 SELECT | ✅ |
| 9 | PRAGMA foreign_keys=ON 生效 | ✅ |
| 10 | Discussion factory 默认值正确 | ✅ |
| 11 | Discussion factory 自定义值覆盖 | ✅ |
| 12 | PanelMember factory 创建 host | ✅ |
| 13 | PanelMember factory 批量创建 experts | ✅ |

---

## 3. 核心组件

### 3.1 MockLLMClient

```
MockLLMClient
├── set_chat_response(text)          → chat() 返回固定文本
├── set_stream_tokens([t1, t2, ...]) → chat_stream() 逐 token yield
├── set_json_response(dict)          → chat_json() 返回固定结构
├── set_fail(count, message)         → 前 count 次抛 LLMAPIError
└── _call_history                    → 记录所有调用 (method + messages + kwargs)
```

**合约**: Agent 单元测试期间，所有 LLM 调用通过 MockLLMClient，零次真实 API 请求。

### 3.2 Async Test Database

```
async_engine          → sqlite+aiosqlite:///:memory: (WAL + FK ON)
async_session_factory → async_sessionmaker(engine, expire_on_commit=False)
db_session            → 单次测试 session，结束自动 rollback
```

每测试独立内存 SQLite，零文件系统交互，零残留数据。

### 3.3 Factories

```
make_discussion_row(...)          → 完整 discussions 表行
make_host_row(discussion_id, ...) → 快速创建主持人
make_expert_rows(discussion_id, count) → 批量创建 2-8 位专家
```

---

## 4. 为 Phase 1 准备

Phase 1 将在此基础设施上执行严格 RED→GREEN→REFACTOR：

- **config.py** → 使用 `pytest` 验证 Settings 默认值和 `.env` 覆盖
- **database.py** → 使用 `async_engine` fixture 创建真实 DB 引擎
- **models/** → 使用 `db_session` fixture 创建表并验证约束

---

## 5. 验收确认

- [x] MockLLMClient 三个接口 (chat/chat_stream/chat_json) 均可控可验证
- [x] 异步 SQLite 引擎正常工作
- [x] 测试工厂提供可信测试数据
- [x] 零处生产代码
- [x] 为 Phase 1 做好全部基础设施准备
