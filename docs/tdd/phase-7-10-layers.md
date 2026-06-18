# Phase 7-10 — Schemas + Services + Routes + WebSocket 测试报告

> **阶段**: TDD  
> **日期**: 2026-06-18  
> **状态**: ✅ PASSED (124/124 累计)

---

## 1. 交付物汇总

| Phase | 层 | 新增测试 | 新增文件 |
|-------|----|---------|----------|
| 7 | Pydantic Schemas | 17 passed | `schemas/{common,discussion,panel,utterance,consensus,ws_events}.py` |
| 8 | Services | — | `services/{discussion_service,panel_service}.py` |
| 9 | API Routes | — | `api/{router,discussions,panel,ws}.py` |
| 10 | App + 集成测试 | 7 passed | `main.py` + `tests/integration/test_api.py` |

---

## 2. 完整测试矩阵

```
tests/unit/: 117 passed
  test_config.py .............. 8
  test_database.py ............. 5
  test_infrastructure.py ...... 13
  test_models.py .............. 22
  test_scheduler.py ........... 12
  test_llm_client.py .......... 11
  test_expert_agent.py ......... 8
  test_host_agent.py ........... 7
  test_observer_agent.py ....... 6
  test_schemas.py ............. 17
  test_discussion_runner.py .... 8

tests/integration/: 7 passed
  test_api.py .................. 7
    - test_create_discussion
    - test_full_flow (create → list → detail → end → report)
    - test_non_creator_cannot_control
    - test_cannot_end_already_ended
    - test_nonexistent_discussion
    - test_health
```

---

## 3. 新增生产代码文件

| 文件 | 描述 |
|------|------|
| `app/schemas/common.py` | `ApiResponse<T>`, `PaginatedList<T>` |
| `app/schemas/discussion.py` | `DiscussionCreate`, `DiscussionResponse`, `DiscussionDetailResponse` |
| `app/schemas/panel.py` | `PanelGenerateRequest/Response`, `PanelConfirmRequest` |
| `app/schemas/utterance.py` | `UtteranceResponse` |
| `app/schemas/consensus.py` | `ConsensusResponse` |
| `app/schemas/ws_events.py` | `WsExpertStatusData`, `WsUtteranceTokenData`, `WsUtteranceCompleteData`, `WsConsensusUpdateData`, `WsDiscussionEndedData` |
| `app/services/discussion_service.py` | CRUD + 生命周期 + 状态流转 + 权限校验 |
| `app/services/panel_service.py` | LLM 嘉宾生成 + 编辑确认 |
| `app/api/router.py` | 汇总全部子路由 |
| `app/api/discussions.py` | 9 REST 端点 |
| `app/api/panel.py` | 2 REST 端点 |
| `app/api/ws.py` | WebSocket 端点 + EventBus |
| `app/main.py` | FastAPI 应用入口 + CORS + startup |

---

## 4. API 契约对齐

| API_CONTRACT.md 端点 | 路由 | 状态码 | 校验 |
|----------------------|------|--------|------|
| `POST /api/discussions` | ✅ | 201 | ✅ topic/expert_count 校验 |
| `GET /api/discussions` | ✅ | 200 | ✅ status/page/page_size |
| `GET /api/discussions/{id}` | ✅ | 200 | ✅ 40401 |
| `POST /.../panel/generate` | ✅ | 200 | ✅ regenerate_member_id |
| `PUT /.../panel` | ✅ | 200 | ✅ ✅ 确认写入 |
| `POST /.../start/pause/resume/end` | ✅ | 200 | ✅ 状态流转 40301/40901 |
| `GET /.../report` | ✅ | 200 | ✅ transcript+consensus |
| `GET /api/health` | ✅ | 200 | ✅ |
| `WS /ws/discussions/{id}` | ✅ | 101 | ✅ advance/pause/resume/end 命令 |

---

## 5. 后端项目结构（完整）

```
backend/
├── app/
│   ├── main.py                     # FastAPI 入口
│   ├── config.py                   # Settings (Pydantic)
│   ├── api/
│   │   ├── router.py               # 路由汇总
│   │   ├── discussions.py          # 讨论 CRUD + 控制
│   │   ├── panel.py                # 嘉宾生成 + 确认
│   │   └── ws.py                   # WebSocket + EventBus
│   ├── models/
│   │   ├── base.py                 # DeclarativeBase
│   │   ├── discussion.py           # 5 张表模型
│   │   ├── panel_member.py
│   │   ├── utterance.py
│   │   ├── consensus.py
│   │   └── expert_status_log.py
│   ├── schemas/                    # Pydantic 请求/响应
│   │   ├── common.py
│   │   ├── discussion.py
│   │   ├── panel.py
│   │   ├── utterance.py
│   │   ├── consensus.py
│   │   └── ws_events.py
│   ├── services/
│   │   ├── discussion_service.py   # 讨论生命周期
│   │   └── panel_service.py        # 嘉宾管理
│   ├── agents/
│   │   ├── base_agent.py           # AgentProtocol
│   │   ├── scheduler.py            # 欲望值仲裁
│   │   ├── llm_client.py           # DeepSeek API
│   │   ├── expert_agent.py         # 专家 Agent
│   │   ├── host_agent.py           # 主持人 Agent
│   │   ├── observer_agent.py       # 独立观察员
│   │   └── discussion_runner.py    # 讨论引擎
│   ├── db/
│   │   ├── database.py             # engine 工厂
│   │   └── session.py              # FastAPI get_db
│   └── utils/
├── tests/
│   ├── conftest.py                 # MockLLMClient + async engine
│   ├── factories/                  # 测试数据工厂
│   ├── unit/                       # 117 个单元测试
│   └── integration/                # 7 个集成测试
├── data/                           # SQLite 文件
├── pyproject.toml
├── .env                            # API Key (gitignored)
└── .env.example
```

---

## 6. 运行方式

```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

```bash
# 运行全部测试
uv run pytest tests/ -q

# 仅单元测试
uv run pytest tests/unit/

# 仅集成测试
uv run pytest tests/integration/
```
