# AI Panel Studio — 后端工程结构

> **阶段**: SDD  
> **日期**: 2026-06-17

---

## 1. 目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI 应用入口
│   ├── config.py                    # 配置管理（环境变量/Settings）
│   │
│   ├── api/                         # API 路由层（薄层，参数校验+调用 Service）
│   │   ├── __init__.py
│   │   ├── router.py                # 汇总所有子路由
│   │   ├── discussions.py           # 讨论 CRUD 端点
│   │   ├── panel.py                 # 嘉宾阵容端点
│   │   └── ws.py                    # WebSocket 端点
│   │
│   ├── models/                      # SQLAlchemy 数据模型（DDL定义）
│   │   ├── __init__.py
│   │   ├── discussion.py            # Discussion
│   │   ├── panel_member.py          # PanelMember
│   │   ├── utterance.py             # Utterance
│   │   ├── consensus.py             # ConsensusDisagreement
│   │   └── expert_status_log.py     # ExpertStatusLog
│   │
│   ├── schemas/                     # Pydantic 请求/响应 Schema（API契约）
│   │   ├── __init__.py
│   │   ├── discussion.py            # DiscussionCreate, DiscussionResponse, DiscussionList
│   │   ├── panel.py                 # PanelGenerateRequest, PanelConfirmRequest, PanelResponse
│   │   ├── utterance.py             # UtteranceResponse
│   │   ├── consensus.py             # ConsensusResponse
│   │   ├── ws_events.py             # WebSocket 事件类型定义
│   │   └── common.py                # ApiResponse, PaginatedList, ErrorResponse
│   │
│   ├── services/                    # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── discussion_service.py    # 讨论生命周期管理
│   │   ├── panel_service.py         # 嘉宾生成 + 编辑确认
│   │   └── report_service.py        # 讨论报告聚合
│   │
│   ├── agents/                      # Agent 编排核心
│   │   ├── __init__.py
│   │   ├── llm_client.py            # DeepSeek API 客户端封装
│   │   ├── base_agent.py            # 抽象 Agent 基类
│   │   ├── host_agent.py            # 主持人 Agent
│   │   ├── expert_agent.py          # 专家 Agent
│   │   ├── observer_agent.py        # 独立观察员 Agent
│   │   ├── scheduler.py             # 发言欲望值调度仲裁器
│   │   └── discussion_runner.py     # 讨论运行引擎（生命周期+事件总线）
│   │
│   ├── db/                          # 数据库基础设施
│   │   ├── __init__.py
│   │   ├── database.py              # SQLAlchemy 引擎 + 会话工厂
│   │   └── session.py               # 依赖注入（get_db）
│   │
│   └── utils/                       # 工具
│       ├── __init__.py
│       ├── session_id.py            # Session ID 生成/管理
│       └── color_generator.py       # 嘉宾颜色生成
│
├── data/                            # SQLite 数据文件目录
│   └── .gitkeep
│
├── tests/                           # 测试（TDD 阶段核心产出）
│   ├── __init__.py
│   ├── conftest.py                  # Fixtures
│   ├── unit/                        # 单元测试
│   │   ├── test_scheduler.py        # 欲望值计算与仲裁
│   │   ├── test_agents.py           # Agent prompt 构建
│   │   └── test_observer.py         # 共识/分歧提炼
│   ├── integration/                 # 集成测试
│   │   ├── test_api.py              # REST 端点
│   │   └── test_websocket.py        # WebSocket 流
│   └── e2e/                         # E2E 测试（Playwright，在 frontend+tests）
│
├── pyproject.toml                   # uv 项目配置 + 依赖
├── .env                             # 环境变量（DeepSeek API Key）
├── .env.example                     # 环境变量模板
└── .gitignore
```

---

## 2. 模块划分与职责

### 2.1 api/ — 路由层（Controller）

| 模块 | 职责 | 依赖 |
|------|------|------|
| `discussions.py` | `POST /api/discussions`, `GET /api/discussions`, `GET /api/discussions/{id}`, `POST /.../start|pause|resume|next|end` | `discussion_service` |
| `panel.py` | `POST /.../panel/generate`, `PUT /.../panel` | `panel_service` |
| `ws.py` | `WS /ws/discussions/{id}` — 连接管理、权限校验、双向事件路由 | `discussion_runner` |

**编码规范**: 路由函数仅做参数提取 + 权限校验 + 调用 Service + 返回统一响应。禁止在路由中写业务逻辑。

### 2.2 services/ — 业务逻辑层

| 模块 | 职责 |
|------|------|
| `discussion_service.py` | 讨论生命周期：创建、状态流转校验、列表查询、详情聚合（含 Transcript） |
| `panel_service.py` | LLM 嘉宾生成、嘉宾编辑校验、阵容确认 |
| `report_service.py` | 报告聚合查询：Transcript + 共识/分歧 + 最后一条发言（主持人总结） |

### 2.3 agents/ — Agent 编排核心

这是项目的核心引擎层，实现 Agent-Mediator 模式。

| 模块 | 职责 |
|------|------|
| `llm_client.py` | DeepSeek API 调用封装，支持 `stream=True`。统一 prompt 发送、token 流式返回、错误重试（最多 2 次） |
| `base_agent.py` | Agent 抽象基类。定义接口：`calculate_desire() → float`、`get_focus_summary() → str`、`generate_utterance() → AsyncGenerator[str]` |
| `host_agent.py` | 主持人 Agent。扩展基类，增加开场白、提问、追问、总结的 prompt 模板。主持人在开场/结尾有特殊调度权 |
| `expert_agent.py` | 专家 Agent。根据立场和当前 Transcript，生成 1-2 句发言。计算发言欲望值时考虑：当前话题与自身立场相关度、最近被反驳程度、未发言轮次等 |
| `observer_agent.py` | 独立观察员 Agent。接收完整 Transcript + 已有共识/分歧列表，对最新发言判断是否产生新的共识或分歧。输出结构化判断结果 |
| `scheduler.py` | 欲望值调度仲裁器。每轮收集所有 Agent 的 desire_value，按决断链排序：desire_value ↓ → 关注点时间距离 → 随机。主持人同分优先 |
| `discussion_runner.py` | 讨论运行引擎。管理讨论生命周期：开始→轮次循环→暂停/继续→结束。持有 WebSocket 事件总线，协调 Agent-Scheduler-Observer 的调用顺序 |

### 2.4 db/ — 数据访问层

| 模块 | 职责 |
|------|------|
| `database.py` | 创建 SQLAlchemy async engine、sessionmaker、表创建 |
| `session.py` | FastAPI 依赖注入 `get_db()`，提供 async session，请求结束自动关闭 |

---

## 3. Agent 编排核心设计

### 3.1 Agent 生命周期

```
                   ┌─────────┐
                   │  idle    │
                   └────┬─────┘
                        │ 新发言完成 / 开场信号
                        ▼
                   ┌─────────┐
                   │preparing│  计算 desire_value + focus_summary
                   └────┬─────┘
                        │ Scheduler 选中
                        ▼
                   ┌─────────┐
                   │speaking │  流式生成 utterance
                   └────┬─────┘
                        │ 发言完成
                        ▼
                   ┌─────────┐
                   │  idle    │ (循环)
                   └─────────┘
```

### 3.2 欲望值计算维度（统一标准）

所有角色（含主持人）使用相同维度计算发言欲望值 0.0-1.0：

| 维度 | 权重 | 说明 |
|------|------|------|
| 话题相关度 | 0.35 | 当前讨论焦点与自身立场/领域相关度 |
| 回应需求度 | 0.30 | 上一条发言是否直接/间接涉及本方观点（被点名/被反驳时升高） |
| 沉默补偿 | 0.20 | 连续未发言轮次越多，欲望值越高（防冷场） |
| 观点新鲜度 | 0.15 | 自身是否还有未表达的独特观点 |

主持人额外加一个 **流程权重**（开场、总结时机自动拉满 desire=1.0），以确保流程节点不被跳过。

### 3.3 Observer 工作流程

```
新发言完毕
    │
    ▼
┌─────────────────────────────┐
│ Observer Agent 接收:         │
│ - 完整 Transcript           │
│ - 已有共识/分歧列表          │
│ - 最新发言 (utterance)       │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 判断逻辑 (LLM prompt):       │
│ 1. 新发言是否印证了已有观点？  │
│    → 更新/增强已有共识        │
│ 2. 新发言是否与已有观点冲突？  │
│    → 创建新分歧               │
│ 3. 新发言是否提出了新观点？    │
│    → 暂存，等后续发言验证      │
│ 4. 是否有分歧被化解？         │
│    → 标记 is_resolved         │
└─────────────┬───────────────┘
              │
              ▼
    WebSocket: consensus_update
    数据库: 写入/更新
```

### 3.4 DiscussionRunner 调度循环

```
async def run_discussion(discussion_id):
    await emit_opening()         # 主持人开场白
    while not should_end():
        await check_pause()      # 如果暂停则阻塞等待
        winner = await scheduler.select_speaker()
        async for token in winner.generate_utterance():
            await ws_broadcast(token)
        await observer_analyze()
        await increment_round()
    await host_summary()         # 主持人总结
    await end_discussion()
```

---

## 4. API 模块与 Service 映射

| API 端点 | 路由模块 | Service 方法 |
|----------|----------|-------------|
| `POST /api/discussions` | `api/discussions.py` | `DiscussionService.create()` |
| `GET /api/discussions` | `api/discussions.py` | `DiscussionService.list_all()` |
| `GET /api/discussions/{id}` | `api/discussions.py` | `DiscussionService.get_detail()` |
| `POST /.../panel/generate` | `api/panel.py` | `PanelService.generate_panel()` |
| `PUT /.../panel` | `api/panel.py` | `PanelService.confirm_panel()` |
| `POST /.../start` | `api/discussions.py` | `DiscussionService.start()` → `DiscussionRunner.run()` |
| `POST /.../pause` | `api/discussions.py` | `DiscussionService.pause()` |
| `POST /.../resume` | `api/discussions.py` | `DiscussionService.resume()` |
| `POST /.../next` | `api/discussions.py` | `DiscussionService.advance_round()` |
| `POST /.../end` | `api/discussions.py` | `DiscussionService.end()` |
| `GET /.../report` | `api/discussions.py` | `ReportService.generate_report()` |
| `WS /ws/discussions/{id}` | `api/ws.py` | `DiscussionRunner.ws_handler()` |

---

## 5. 数据库模型汇总

| 模型类 | 对应表 | 文件 |
|--------|--------|------|
| `Discussion` | `discussions` | `models/discussion.py` |
| `PanelMember` | `panel_members` | `models/panel_member.py` |
| `Utterance` | `utterances` | `models/utterance.py` |
| `ConsensusDisagreement` | `consensus_disagreements` | `models/consensus.py` |
| `ExpertStatusLog` | `expert_status_logs` | `models/expert_status_log.py` |

所有模型使用 SQLAlchemy 2.0 声明式映射（`mapped_column` + `Mapped[]`）。

---

## 6. 配置管理

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # DeepSeek
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/ai_panel_studio.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Discussion
    default_expert_count: int = 4
    min_expert_count: int = 2
    max_expert_count: int = 8
    default_max_rounds: int | None = None
    auto_end_threshold: int = 3
    llm_max_retries: int = 2

    class Config:
        env_file = ".env"
```
