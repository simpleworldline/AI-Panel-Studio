# AI Panel Studio — 实施计划

> **阶段**: SDD  
> **日期**: 2026-06-17  
> **方法论**: SDD → DDD → TDD 多范式融合

---

## 1. 开发阶段总览

```
Phase 1 ──── Phase 2 ──── Phase 3 ──── Phase 4 ──── Phase 5
 脚手架      SDD 实现      DDD 实现      TDD 实现      交付
 (1天)       (2天)         (3天)         (3天)         (1天)
```

| Phase | 名称 | 方法论 | 产出 |
|-------|------|--------|------|
| 1 | 项目脚手架 | — | 前后端项目骨架、构建配置、目录结构 |
| 2 | 数据与契约落地 | SDD | DB 建表、API 端点、WebSocket 基础框架 |
| 3 | UI 设计与交互 | DDD | UI UX Pro Max 输出 + 前端组件实现 |
| 4 | 测试驱动验证 | TDD | 单元测试 + 集成测试 + E2E 测试 |
| 5 | 集成与交付 | — | 联调、修 bug、部署文档 |

---

## 2. Phase 1: 项目脚手架

**目标**: 建立可运行的空应用骨架，前后端可通信。

### 2.1 交付物

| # | 交付物 | 描述 |
|---|--------|------|
| 1.1 | 前端项目骨架 | Vite + React + TypeScript + Tailwind + 路由框架 |
| 1.2 | 后端项目骨架 | FastAPI + uv + SQLAlchemy + 目录结构 |
| 1.3 | 数据库初始化 | SQLAlchemy 引擎 + 会话工厂 + 自动建表 |
| 1.4 | 环境变量模板 | `.env.example` + `config.py` |
| 1.5 | Hello World 验证 | `GET /api/health` 返回 200，前端可调通 |

### 2.2 验收标准

```
✅ 前端 npm run dev 正常启动
✅ 后端 uvicorn 正常启动
✅ GET /api/health → {"code":200,"data":{"status":"ok"}}
✅ 前端 fetch /api/health 成功
✅ Tailwind 编译正常
✅ SQLite 文件成功创建
```

---

## 3. Phase 2: 数据与契约落地 (SDD)

**目标**: 实现所有数据模型、API 端点、WebSocket 基础框架。**不涉及 Agent 业务逻辑**。

### 3.1 交付物

| # | 交付物 | 描述 |
|---|--------|------|
| 2.1 | 数据模型实现 | 5 张表的 SQLAlchemy 模型（Discussion / PanelMember / Utterance / ConsensusDisagreement / ExpertStatusLog） |
| 2.2 | Pydantic Schema | 所有请求/响应 Schema，与 API_CONTRACT.md 严格一致 |
| 2.3 | 讨论 CRUD API | `POST/GET /api/discussions` + `GET /api/discussions/{id}` |
| 2.4 | 讨论控制 API | `POST start|pause|resume|next|end`（状态流转 + 权限校验） |
| 2.5 | 报告 API | `GET /api/discussions/{id}/report` |
| 2.6 | WebSocket 框架 | WebSocket 端点建立连接、Session 校验、事件收发骨架 |
| 2.7 | 错误处理 | 统一错误码 + 全局异常处理器 |

### 3.2 验收标准

```
✅ 所有 API 端点返回格式符合 API_CONTRACT.md
✅ 讨论创建/列表/详情/状态流转正常
✅ 权限校验：非创建者操作返回 403
✅ 状态冲突：已结束讨论不可操作返回 409
✅ WebSocket 连接成功，双向收发正常
✅ 数据库 CRUD 操作通过（手动 curl/Postman 验证）
✅ 所有响应不含 JSON 格式错误
```

---

## 4. Phase 3: UI 设计与交互 (DDD)

**目标**: 使用 UI UX Pro Max 完成演播厅视觉设计 + 前端完整实现。

### 4.1 交付物

| # | 交付物 | 描述 |
|---|--------|------|
| 3.1 | 嘉宾生成功能 | PanelService + Panel API + 前端创建讨论页 + 嘉宾编辑页 |
| 3.2 | 首页 | 讨论列表（进行中/已结束 Tab）、搜索、发起新讨论入口 |
| 3.3 | 演播厅 UI | 三栏响应式布局、专家状态小窗、Transcript 流式显示、共识/分歧面板、控制栏 |
| 3.4 | 讨论报告页 | Transcript 全文 + 共识/分歧汇总 + 主持人总结 |
| 3.5 | 演播厅动效 | 嘉宾状态灯动画、流式打字机效果、共识/分歧插入动画 |
| 3.6 | UI UX Pro Max 视觉 | 演播厅深色主题、嘉宾颜色标识、电视节目风格 |

### 4.2 验收标准

```
✅ 完整用户流程：创建→编辑→确认→演播厅→报告 可走通
✅ 响应式布局：三栏/两栏/单栏三种模式切换正常
✅ 各区域独立滚动，不互相影响
✅ 嘉宾颜色在全局一致（卡片/Transcript/状态灯）
✅ 中文 UI 文案审查通过（无英文残留）
✅ UI UX Pro Max 设计稿与实现一致性 > 90%
```

---

## 5. Phase 4: 测试驱动验证 (TDD)

**目标**: 严格 TDD 流程 — 先写测试（红灯），实现 Agent 逻辑（绿灯），重构。

### 5.1 单元测试

| # | 测试对象 | 测试点 |
|---|----------|--------|
| 4.1 | `scheduler.py` | 欲望值排序、决断链（值→时间→随机）、主持人同分优先、多人同分随机 |
| 4.2 | `expert_agent.py` | 欲望值计算四维度、发言长度 1-2 句、prompt 不泄露 CoT |
| 4.3 | `host_agent.py` | 开场白生成、总结生成、追问欲望值计算、流程节点 desire=1.0 |
| 4.4 | `observer_agent.py` | 共识检测、分歧检测、置信度输出、增量更新 |
| 4.5 | `llm_client.py` | API 调用格式正确、stream 逐 token 返回、重试机制 |

### 5.2 集成测试

| # | 测试对象 | 测试点 |
|---|----------|--------|
| 4.6 | Discussion API | 完整生命周期：创建→生成→确认→开始→暂停→继续→结束 |
| 4.7 | WebSocket 流 | 连接→接收 expert_status → 接收 utterance_token → 接收 utterance_complete → 接收 consensus_update → 接收 discussion_ended |
| 4.8 | 权限校验 | 非创建者操作拒绝、Session 校验 |
| 4.9 | 并发隔离 | 同时运行 2 场讨论，状态、Transcript、事件互不干扰 |

### 5.3 E2E 测试 (Playwright)

| # | 测试场景 | 关键断言 |
|---|----------|----------|
| 4.10 | 完整讨论流程 | 首页→创建→生成→编辑→演播厅→观看 3 轮→结束→查看报告 |
| 4.11 | 响应式布局 | 三种宽度下各区域可见且可滚动 |
| 4.12 | 错误处理 | 无效话题、非创建者操作、阵容未确认时开始讨论 |
| 4.13 | 手动控制 | 暂停/继续/手动推进/强制结束 |
| 4.14 | 自动结束 | max_rounds 触发结束 |

### 5.4 验收标准

```
✅ 单元测试覆盖率 > 80%（Agent 核心逻辑 > 90%）
✅ 所有集成测试通过
✅ 所有 E2E 测试通过
✅ 讨论过程中无 JSON 或格式化字符出现在 UI 中
✅ Transcript 不包含"举手"、"思考中"等内部动作
✅ 共识/分歧实时更新（增量模式）
```

---

## 6. Phase 5: 集成与交付

**目标**: 前后端联调、修 bug、部署文档。

### 6.1 交付物

| # | 交付物 | 描述 |
|---|--------|------|
| 5.1 | 联调修复 | 前后端对接所有边界 case |
| 5.2 | 部署文档 | Nginx 配置、uvicorn 启动方式、环境变量配置 |
| 5.3 | README.md | 项目介绍 + 本地开发指南 |
| 5.4 | 性能验证 | 首屏加载 < 3s、WebSocket token 延迟 < 100ms |

### 6.2 验收标准

```
✅ 完整用户故事从头到尾无报错
✅ README 可让新开发者 5 分钟跑起来
✅ 部署文档覆盖生产环境配置
```

---

## 7. 依赖关系图

```
Phase 1: 脚手架
   │
   ▼
Phase 2: SDD (数据+API+WS基础)
   │
   ├──────────────────┐
   ▼                  ▼
Phase 3: DDD        Phase 4: TDD (Agent 单元测试可与DDD并行)
   │                  │
   └────────┬─────────┘
            ▼
      Phase 5: 集成交付
```

---

## 8. 为 TDD 阶段准备

### 8.1 测试基础设施（Phase 2 就位）

在 Phase 2（SDD 实现）阶段即建立测试基础设施：

```
backend/tests/
├── conftest.py           # pytest fixtures: async client, test db, mock llm
├── unit/                 # 占位（Phase 4 填充）
├── integration/          # 占位（Phase 4 填充）
└── factories/            # 测试数据工厂
    ├── discussion_factory.py
    └── panel_member_factory.py

frontend/
└── src/__tests__/        # Vitest 配置（Phase 3 建立，Phase 4 填充）
```

### 8.2 Mock LLM Client（TDD 阶段核心）

```python
# tests/conftest.py 中提供 MockLLMClient
# 支持：
# - 预设发言文本（模拟流式返回）
# - 预设欲望值（模拟 Agent 竞争）
# - 预设共识/分歧判断
# - 调用记录（验证 Agent 调用次数/参数）
```

### 8.3 TDD 工作流

```
1. 写测试 → 红灯 ❌
2. 写最少实现 → 绿灯 ✅  
3. 重构 → 保持绿灯 ✅
4. 提交（code + test 同 commit）
```

每个 Agent 模块遵循此循环：test → implement → refactor → commit。

---

## 9. 时间估算

| Phase | 预估工时 | 关键风险 |
|-------|----------|----------|
| 1. 脚手架 | 0.5 天 | 低 |
| 2. SDD 实现 | 2 天 | 低 — 纯 CRUD + 契约 |
| 3. DDD 实现 | 3 天 | 中 — UI UX Pro Max 视觉实现复杂度、Agent 业务逻辑 |
| 4. TDD 实现 | 3 天 | 中 — Agent 调度逻辑不确定性、E2E 稳定性 |
| 5. 集成交付 | 1 天 | 低 |
| **总计** | **~9.5 天** | |

---

## 10. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| DeepSeek API 响应慢/不稳定 | Agent 发言延迟大 | llm_client 内置重试 + 超时保护；Mock 模式可无 LLM 调试 |
| Agent 发言质量不可控 | 讨论内容无聊或重复 | Prompt 工程迭代（TDD 阶段重点验证）；欲望值沉默补偿防冷场 |
| WebSocket 并发连接数 | 多讨论时资源占用 | MVP 限制每 Session 最多 3 个并发讨论；异步连接池 |
| SQLite 并发写瓶颈 | 多人同时观看写入冲突 | WAL 模式 + 单进程运行，MVP 可接受 |
