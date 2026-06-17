# AI Panel Studio — 技术选型文档

> **阶段**: SDD  
> **日期**: 2026-06-17  
> **状态**: 已确认

---

## 1. 技术栈总览

```
┌────────────────────────────────────────────────────┐
│                    前端 (Frontend)                  │
│  Vite 5  +  React 18  +  TypeScript 5              │
│  React Router 6  +  Zustand 4  +  Tailwind CSS 3   │
│  WebSocket (native)  +  Axios                       │
└────────────────────────┬───────────────────────────┘
                         │ HTTP REST + WebSocket
┌────────────────────────┴───────────────────────────┐
│                    后端 (Backend)                    │
│  Python 3.12  +  FastAPI 0.115  +  uv              │
│  SQLAlchemy 2  +  aiosqlite  +  Pydantic 2         │
│  httpx (async)  +  asyncio                          │
└────────────────────────┬───────────────────────────┘
                         │ HTTPS
┌────────────────────────┴───────────────────────────┐
│                外部服务 (External)                   │
│  DeepSeek API (deepseek-chat)                       │
│  https://api.deepseek.com/v1                        │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────┴──────────────────────────────┐
│                数据存储 (Storage)                    │
│  SQLite (via aiosqlite, async)                      │
└─────────────────────────────────────────────────────┘
```

---

## 2. 前端技术选型

### 2.1 核心框架

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| **Vite** | ^5.4 | 极快的 HMR 冷启动，原生 ESM 开发体验，Rollup 生产构建，React 插件生态成熟 |
| **React** | ^18.3 | 生态最大、社区最活跃的 UI 库，并发特性(useTransition)适配流式更新场景 |
| **TypeScript** | ^5.5 | 全栈类型安全，与后端 Pydantic 共享类型心智模型，减少运行时错误 |

### 2.2 路由与状态管理

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| **React Router** | ^6.26 | 声明式路由，嵌套布局支持，loader/action 模式，适合多页面应用 |
| **Zustand** | ^4.5 | 极轻量（<1KB），无 boilerplate，支持中间件(persist/devtools)，天然适配 WebSocket 事件驱动的状态更新 |

**为什么不用 Redux/MobX**: 本项目状态模型相对集中（讨论状态、演播厅实时状态），不需要 Redux 的样板代码量。Zustand 的 `set()` 直接合并状态，与 WebSocket 事件推送一一对应。

### 2.3 样式方案

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| **Tailwind CSS** | ^3.4 | 原子化 CSS，响应式断点原生支持（`lg:`/`md:`/`sm:` 直接映射三栏/两栏/单栏），暗色主题开箱即用，适合演播厅视觉风格 |

### 2.4 HTTP 与 WebSocket

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| **Axios** | ^1.7 | REST API 调用，拦截器支持错误统一处理 |
| **浏览器原生 WebSocket** | — | 零依赖，React 自定义 Hook 封装即可，无需 Socket.IO 的重连/房间等重量特性 |

---

## 3. 后端技术选型

### 3.1 核心框架

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| **Python** | 3.12+ | 生态成熟，asyncio 原生支持良好，AI/LLM SDK 生态丰富 |
| **FastAPI** | ^0.115 | 原生 async/await，原生 WebSocket 支持，自动 OpenAPI 生成，Pydantic 深度集成。是构建实时 Agent 系统的最佳 Python 框架 |
| **uv** | latest | PRD 指定，Rust 编写的极速包管理器，替代 pip + venv |

### 3.2 数据库

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| **SQLite** | 3 (via aiosqlite) | PRD 指定。零配置、文件级数据库，async 驱动适配 FastAPI 异步模型，单机部署足够 |
| **SQLAlchemy** | ^2.0 | Python 最成熟的 ORM，2.0 原生 async 支持，声明式模型定义，迁移工具(alembic)可选 |
| **aiosqlite** | ^0.20 | SQLite 的 asyncio 驱动，与 SQLAlchemy async 引擎配合 |

### 3.3 外部 API 调用

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| **httpx** | ^0.27 | 全功能 async HTTP 客户端，支持 HTTP/2，流式响应，用于调用 DeepSeek API（支持 streaming） |
| **DeepSeek API** | deepseek-chat | PRD 指定。128K 上下文窗口，兼容 OpenAI SDK 格式，`stream=True` 实现逐 token 推送 |

### 3.4 数据验证

| 技术 | 版本 | 选型理由 |
|------|------|----------|
| **Pydantic** | ^2.8 | FastAPI 原生集成，请求/响应自动校验，JSON Schema 自动生成，与 TypeScript 接口可自动同步 |

---

## 4. 开发工具链

| 工具 | 用途 |
|------|------|
| **pytest** + **pytest-asyncio** | 后端单元/集成测试 |
| **Vitest** | 前端单元测试（与 Vite 共享配置） |
| **Playwright** | E2E 端到端测试（TDD 阶段核心工具） |
| **Ruff** | Python 代码格式化和 Lint（替代 flake8 + black） |
| **ESLint** + **Prettier** | 前端代码规范 |
| **alembic** (可选) | 数据库迁移管理 |

---

## 5. 部署方案 (MVP)

| 组件 | 方案 | 说明 |
|------|------|------|
| **前端** | Vite 构建静态文件，Nginx 托管 | SPA 模式，所有路由 fallback 到 index.html |
| **后端** | `uvicorn` 单进程运行 FastAPI | MVP 阶段单进程即可承载有限并发讨论 |
| **数据库** | SQLite 文件 | 与后端同机部署，路径通过环境变量配置 |
| **反向代理** | Nginx | 统一入口，`/api` 代理到后端，`/ws` 升级 WebSocket，其余静态文件 |

---

## 6. 技术约束与边界

| 约束 | 决策 |
|------|------|
| API Key 管理 | 仅在 `backend/.env` 读取，nginx 不转发该路径 |
| 并发隔离 | 每个 Discussion 在内存中维护独立 Agent 实例和事件队列 |
| LLM 调用频率 | 每次讨论最大并发 LLM 调用数 = 角色数 + 1（观察员），通过 asyncio.Semaphore 限流 |
| 数据库并发 | SQLite WAL 模式，单写多读 |
| 无外部依赖 | MVP 不依赖 Redis、MQ 等外部中间件 |
