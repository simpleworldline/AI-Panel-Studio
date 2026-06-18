# AI Panel Studio

> AI 驱动的圆桌讨论演播厅。输入话题，LLM 自动生成嘉宾阵容，观看一场 AI 驱动的实时圆桌讨论。

---

## 目录

- [快速开始](#快速开始)
- [环境变量配置](#环境变量配置)
- [技术选型](#技术选型)
- [项目结构](#项目结构)
- [主要 API 列表](#主要-api-列表)
- [已完成能力](#已完成能力)
- [后续改进方向](#后续改进方向)

---

## 快速开始

### 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | ≥ 3.12 | 后端运行环境 |
| uv | latest | Python 包管理器 |
| Node.js | ≥ 18 | 前端运行环境 |
| npm | ≥ 9 | 前端包管理器 |

### 1. 克隆项目

```bash
git clone https://github.com/simpleworldline/AI-Panel-Studio.git
cd AI-Panel-Studio
```

### 2. 启动后端

```bash
cd backend

# 安装依赖（首次运行）
uv sync

# 启动后端（开发模式，代码变更自动重启）
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端启动后可访问：
- **API 服务**: http://localhost:8000
- **OpenAPI 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health

### 3. 启动前端

```bash
cd frontend

# 安装依赖（首次运行）
npm install

# 启动前端（开发模式）
npm run dev
```

前端启动后访问：**http://localhost:5173**

> Vite 开发服务器已配置代理：`/api` → `http://localhost:8000`，`/ws` → `ws://localhost:8000`

### 4. 运行测试

```bash
# 后端测试（116 test cases）
cd backend && uv run python -m pytest -v

# 前端测试（119 test cases）
cd frontend && npx vitest run
```

---

## 环境变量配置

后端通过 `backend/.env` 文件配置环境变量：

```bash
# backend/.env

# DeepSeek API（必填）
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# 数据库（SQLite 文件路径）
DATABASE_URL=sqlite+aiosqlite:///./data/ai_panel_studio.db

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 讨论默认参数
DEFAULT_EXPERT_COUNT=4      # 默认嘉宾人数
MIN_EXPERT_COUNT=2           # 最少嘉宾人数
MAX_EXPERT_COUNT=8           # 最多嘉宾人数
AUTO_END_THRESHOLD=3         # 连续无共识自动结束阈值
LLM_MAX_RETRIES=2            # LLM 调用最大重试次数
```

> 参考模板文件：`backend/.env.example`

---

## 技术选型

### 前端

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| **Vite** | ^8.0 | 极速 HMR，原生 ESM 开发体验 |
| **React** | ^19.2 | 生态最大，并发特性适配流式更新 |
| **TypeScript** | ^6.0 | 全栈类型安全 |
| **React Router** | ^7.18 | 声明式路由，嵌套布局 |
| **Zustand** | ^5.0 | 极轻量状态管理，适配 WebSocket 事件驱动 |
| **Tailwind CSS** | ^4.3 | 原子化 CSS，响应式断点原生支持 |
| **Axios** | ^1.18 | REST API 调用 + 拦截器 |
| **Vitest** | ^4.1 | 单元测试（与 Vite 共享配置） |

### 后端

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| **Python** | 3.12+ | asyncio 原生支持，LLM/AI SDK 生态 |
| **FastAPI** | ^0.137 | 原生 async/await + WebSocket + 自动 OpenAPI |
| **SQLAlchemy** | ^2.0 | Python 最成熟 ORM，2.0 原生 async |
| **aiosqlite** | ^0.22 | SQLite 异步驱动 |
| **Pydantic** | ^2.13 | FastAPI 原生集成，自动请求/响应校验 |
| **httpx** | ^0.28 | 全功能 async HTTP 客户端 |
| **uv** | latest | Rust 编写的极速包管理器 |

### 外部服务

| 服务 | 用途 |
|------|------|
| **DeepSeek API** (`deepseek-chat`) | LLM 嘉宾生成 + Agent 对话 + 共识提炼 |

### 架构模式

**Agent-Mediator**: 每个角色（主持人/专家/观察员）是独立 Agent，持有 Transcript 只读副本，通过 Scheduler 发言欲望值调度器竞争发言权，实现去中心化的非机械轮替讨论。

---

## 项目结构

```
AI-Panel-Studio/
├── README.md
├── backend/
│   ├── app/
│   │   ├── main.py                      # FastAPI 入口 + 全局错误处理
│   │   ├── config.py                    # 环境变量配置
│   │   ├── api/                         # API 路由层
│   │   │   ├── discussions.py           # 12个REST端点（CRUD+控制+报告）
│   │   │   ├── panel.py                 # 嘉宾阵容端点
│   │   │   └── ws.py                    # WebSocket + ConnectionManager
│   │   ├── agents/                      # Agent 编排核心
│   │   │   ├── llm_client.py            # DeepSeek API 封装
│   │   │   ├── base_agent.py            # Agent 抽象基类
│   │   │   ├── host_agent.py            # 主持人 Agent
│   │   │   ├── expert_agent.py          # 专家 Agent
│   │   │   ├── observer_agent.py        # 独立观察员 Agent
│   │   │   ├── scheduler.py             # 发言欲望值调度仲裁器
│   │   │   └── discussion_runner.py     # 讨论运行引擎
│   │   ├── models/                      # SQLAlchemy 数据模型
│   │   │   ├── discussion.py
│   │   │   ├── panel_member.py
│   │   │   ├── utterance.py
│   │   │   ├── consensus.py
│   │   │   └── expert_status_log.py
│   │   ├── schemas/                     # Pydantic 请求/响应 Schema
│   │   ├── services/                    # 业务逻辑层
│   │   │   ├── discussion_service.py    # 讨论生命周期管理
│   │   │   ├── panel_service.py         # LLM 嘉宾生成 + 编辑确认
│   │   │   ├── report_service.py        # 讨论报告聚合
│   │   │   └── runner_registry.py       # Runner 全局注册表
│   │   ├── db/                          # 数据库基础设施
│   │   └── utils/
│   ├── data/                            # SQLite 数据文件
│   ├── tests/
│   │   ├── unit/                        # 单元测试（37 test cases）
│   │   ├── integration/                 # 集成测试（24 test cases）
│   │   ├── e2e/                         # E2E 测试（25 test cases）
│   │   └── factories/                   # 测试数据工厂
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/          # API 客户端
│   │   ├── components/   # UI 组件（19 个）
│   │   ├── pages/        # 页面（5 个）
│   │   ├── store/        # Zustand 状态管理
│   │   ├── types/        # TypeScript 类型
│   │   ├── utils/        # 工具函数
│   │   └── ws/           # WebSocket 客户端
│   └── tests/
└── docs/
    ├── PRD.md            # 产品需求文档
    ├── sdd/               # 设计文档（8份）
    ├── ddd/               # DDD 阶段文档
    ├── tdd/               # TDD 阶段文档
    ├── api/               # API 文档
    └── e2e/               # E2E 测试文档
```

---

## 主要 API 列表

### REST API（12 个端点）

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| `GET` | `/api/health` | 健康检查 | 公开 |
| `POST` | `/api/discussions` | 创建讨论 | 公开（含 Session 头） |
| `GET` | `/api/discussions` | 讨论列表（分页+按状态筛选） | 公开 |
| `GET` | `/api/discussions/{id}` | 讨论详情（含嘉宾/发言/共识） | 公开 |
| `POST` | `/api/discussions/{id}/start` | 开始讨论 | 创建者 |
| `POST` | `/api/discussions/{id}/pause` | 暂停讨论 | 创建者 |
| `POST` | `/api/discussions/{id}/resume` | 继续讨论 | 创建者 |
| `POST` | `/api/discussions/{id}/next` | 手动推进发言 | 创建者 |
| `POST` | `/api/discussions/{id}/end` | 结束讨论 | 创建者 |
| `POST` | `/api/discussions/{id}/panel/generate` | LLM 生成嘉宾阵容 | 公开 |
| `PUT` | `/api/discussions/{id}/panel` | 确认/编辑嘉宾阵容 | 创建者 |
| `GET` | `/api/discussions/{id}/report` | 讨论报告 | 公开 |

### WebSocket 事件

| 事件 | 方向 | 说明 |
|------|------|------|
| `expert_status` | S→C | 嘉宾状态实时变更（idle/preparing/speaking） |
| `utterance_token` | S→C | 流式发言逐 token 推送 |
| `utterance_complete` | S→C | 发言完成（含完整内容和元数据） |
| `consensus_update` | S→C | 共识/分歧实时更新 |
| `discussion_paused` | S→C | 讨论暂停通知 |
| `discussion_resumed` | S→C | 讨论继续通知 |
| `discussion_ended` | S→C | 讨论结束通知（含结束原因和统计） |
| `initial_snapshot` | S→C | 连接时发送的当前完整状态 |
| `advance` | C→S | 手动推进发言 |
| `pause` | C→S | 暂停讨论 |
| `resume` | C→S | 继续讨论 |
| `end` | C→S | 强制结束讨论 |

> 完整 API 文档见 [docs/api/BACKEND_API.md](docs/api/BACKEND_API.md) 和 [docs/api/README.md](docs/api/README.md)

---

## 已完成能力

### 核心功能

- [x] **讨论创建**: 输入话题（1-200字）、选择嘉宾人数（2-8人）、自定义发言上限
- [x] **LLM 嘉宾生成**: DeepSeek API 实时生成 1 位主持人 + N 位专家（含姓名/职业/立场/专属颜色）
- [x] **嘉宾编辑**: 编辑姓名/Title/立场/颜色，单体/全体重新生成
- [x] **演播厅实时讨论**: AI 驱动的圆桌讨论，WebSocket 实时推送

### Agent 编排

- [x] **非机械轮替发言**: 欲望值调度器（话题相关度、回应需求度、沉默补偿、观点新鲜度）
- [x] **主持人**: 开场白、提问串场、追问介入、最终总结
- [x] **专家**: 自主举手/反驳/补充，每次 1-2 句
- [x] **独立观察员**: 实时提炼共识与分歧（含置信度）
- [x] **辩论窗口模式**: 同一话题下的追问/反驳嵌套显示

### 用户体验

- [x] **响应式布局**: 三栏（≥1400px）/ 两栏（≥800px）/ 单栏（<800px）
- [x] **各区域独立滚动**: 嘉宾状态、Transcript、共识/分歧各栏不互相影响
- [x] **流式打字机效果**: 发言逐 token 实时展示
- [x] **嘉宾状态指示灯**: idle（灰）→ preparing（黄）→ speaking（蓝）
- [x] **线程式对话**: 追问/反驳缩进显示在原始言论下方
- [x] **全中文 UI**: 按钮/标签/提示/错误信息均为中文
- [x] **Toast 通知**: 成功/错误/信息提示居中显示，3秒自动消失

### 讨论控制

- [x] **手动推进**: 用户可触发发言
- [x] **暂停/继续**: 当前发言完成后立即生效
- [x] **强制结束**: 立即标记结束 + 移除 Agent
- [x] **自然结束**: 达到发言上限时主持人总结后自动结束
- [x] **首页状态筛选**: 进行中（live+paused）/ 待开始（pending）/ 已结束（ended）

### 数据与存储

- [x] **SQLite 持久化**: 5张表（discussions / panel_members / utterances / consensus_disagreements / expert_status_logs）
- [x] **跨重启数据保留**: WAL 模式 + 文件持久化
- [x] **多讨论并发隔离**: 各讨论独立 Agent 实例和事件队列
- [x] **创建者权限控制**: X-Session-Id 标识，非创建者仅可观看

### 讨论报告

- [x] **完整 Transcript**: 按发言顺序记录所有发言
- [x] **共识汇总**: 已达成共识的列表
- [x] **分歧汇总**: 已产生分歧的列表（含是否已化解）
- [x] **主持人总结**: LLM 生成的自然语言总结

### 测试

- [x] **后端单元测试**: 63（数据库模型 + Schema + Scheduler + LLM Panel）
- [x] **后端集成测试**: 24（REST API + 错误处理）
- [x] **后端 E2E 测试**: 25（完整用户流程）
- [x] **前端测试**: 119（组件 + Store + 工具函数）
- [x] **测试覆盖**: 231 个测试全程自动化

---

## 后续改进方向

### v1.1 候选功能

- [ ] **讨论回放**: 时间轴拖动回看已结束讨论
- [ ] **嘉宾头像生成**: 调用文生图 API 生成嘉宾头像
- [ ] **用户认证系统**: 注册/登录 + 历史讨论管理
- [ ] **讨论分享**: 生成可分享的讨论链接/二维码
- [ ] **iframe 嵌入**: 支持将演播厅嵌入第三方网站

### 性能优化

- [ ] **LLM 调用优化**: 批量请求合并、连接池复用、响应缓存
- [ ] **WebSocket 状态压缩**: 减少重复状态推送
- [ ] **前端虚拟列表**: 大量发言时使用虚拟滚动
- [ ] **数据库索引优化**: 高频查询添加复合索引

### 架构升级

- [ ] **Redis 集成**: Session 管理 + 讨论状态缓存 + 发布订阅
- [ ] **PostgreSQL 迁移**: 生产环境数据库升级
- [ ] **Docker 部署**: 容器化部署方案
- [ ] **CI/CD**: GitHub Actions 自动化测试 + 部署
- [ ] **多语言支持**: i18n 国际化（英文 + 日文）
- [ ] **后台管理面板**: 讨论管理 + 数据统计 + 系统监控

### 体验增强

- [ ] **嘉宾 3D 头像**: 三渲二或 Live2D 风格头像
- [ ] **语音合成**: 发言内容文字转语音（TTS）
- [ ] **讨论主题自定义**: 用户自定义演播厅主题/背景色
- [ ] **发言人情绪表达**: 为发言附加情绪标签
- [ ] **讨论摘要导出**: PDF/Markdown 格式导出
- [ ] **讨论模板**: 预设话题模板快速发起讨论

---

## 开发方法论

本项目采用 **多范式融合工程化架构**：

| 阶段 | 方法 | 核心产出 |
|------|------|----------|
| **前期** | PRD（产品需求定义） | 需求文档、用户故事 |
| **中期** | SDD（Spec/Schema-Driven） | 数据模型 DDL、API 契约、WebSocket 事件 Schema |
| **中期** | DDD（Design-Driven） | UI 设计、组件树、状态流转、交互规范 |
| **后期** | TDD（Test-Driven） | 单元测试、集成测试、E2E 测试（231 cases） |

---

## 许可证

MIT License

---

## 贡献

欢迎提交 Issue 和 Pull Request。
