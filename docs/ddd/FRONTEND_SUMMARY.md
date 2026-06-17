# AI Panel Studio — 前端开发总结

> **阶段**: DDD  
> **日期**: 2026-06-17  
> **技术栈**: Vite 8 + React 18 + TypeScript 5 + Tailwind CSS 4 + Zustand 4

---

## 1. 项目统计

```
frontend/src/
├── api/         2 files   99 lines    REST API 封装
├── ws/          1 file    75 lines    WebSocket 客户端
├── types/       4 files  283 lines    TypeScript 类型定义
├── utils/       2 files   49 lines    工具函数
├── store/       4 files  481 lines    Zustand 状态管理
├── hooks/       1 file     7 lines    自定义 Hook
├── components/ 16 files  713 lines    UI 组件
│   ├── ui/      7 files  262 lines    基础原子组件
│   └──          9 files  451 lines    业务组件
├── layouts/     1 file    32 lines    全局布局
├── pages/       4 files  856 lines    页面组件
├── App.tsx      1 file    23 lines    路由定义
├── main.tsx     1 file     5 lines    入口
└── index.css    1 file    43 lines    设计系统

总计: 40 个 TS/TSX 文件, ~2,666 行代码
构建: Vite build 253ms, 112 modules
类型: npx tsc --noEmit 零错误
```

---

## 2. 架构分层

```
┌──────────────────────────────────────────────┐
│  pages/         路由入口，薄层组合              │
│  HomePage / PanelSetupPage / StudioPage /     │
│  ReportPage                                   │
├──────────────────────────────────────────────┤
│  components/    纯 UI 组件，Props 驱动          │
│  ExpertCard / UtteranceItem / ControlBar /    │
│  ConsensusPanel / TranscriptView / ...        │
├──────────────────────────────────────────────┤
│  store/         Zustand 状态管理               │
│  useDiscussionStore / usePanelStore /         │
│  useStudioStore / useToastStore               │
├──────────────────────────────────────────────┤
│  api/ + ws/     通信层                        │
│  discussions.ts / panel.ts / wsClient.ts      │
├──────────────────────────────────────────────┤
│  types/         TypeScript 类型定义             │
│  discussion / consensus / expert / ws         │
└──────────────────────────────────────────────┘
```

---

## 3. 已实现页面

| 路由 | 页面 | 状态 |
|------|------|------|
| `/` | HomePage — 讨论广场 + 创建讨论 Modal | ✅ 完整 |
| `/create/:id/panel` | PanelSetupPage — 嘉宾阵容编辑 | ✅ 完整 |
| `/studio/:id` | StudioPage — 演播厅实时讨论 | ✅ 完整 |
| `/report/:id` | ReportPage — 讨论总结报告 | ✅ 完整 |

---

## 4. 已实现组件

### 基础原子组件 (7 个)

| 组件 | 功能 |
|------|------|
| `Button` | 4 变体 (primary/secondary/danger/ghost) + 2 尺寸 + loading |
| `Input` | 受控输入 + 错误态 |
| `Modal` | 遮罩 + ESC 关闭 + 3 尺寸 |
| `Toast` | 4 类型 (success/error/warning/info) + 自动消失 |
| `Spinner` | 3 尺寸 loading 动画 |
| `Badge` | 7 变体 (live/ended/consensus/disagreement/idle/preparing/speaking) |
| `ColorPicker` | 15 预设色 + 自定义 HEX 输入 |

### 业务组件 (9 个)

| 组件 | 功能 |
|------|------|
| `DiscussionCard` | 讨论卡片 — 话题/专家/轮次/状态/悬停动效 |
| `PanelDots` | 嘉宾颜色圆点展示 |
| `EmptyState` | 空状态引导页 |
| `ExpertCard` | 专家卡片 — 头像/Title/立场/状态灯/欲望值条/关注点摘要 |
| `ExpertStatusPanel` | 专家面板容器 |
| `UtteranceItem` | 单条发言 — 颜色标记/发言人/类型Badge/时间 |
| `StreamingText` | 流式打字机 + 闪烁光标 |
| `TranscriptView` | 转录列表 + 自动滚动 + 流式叠加 |
| `ConsensusItem` | 共识/分歧卡片 — 类型Badge/置信度/已化解标记 |
| `ConsensusPanel` | 共识/分歧面板容器 |
| `ControlBar` | 控制栏 — 暂停/继续/下一轮/结束 + 权限判断 |

---

## 5. 状态管理 (3 Store + 1 Toast)

| Store | 行数 | 职责 |
|-------|------|------|
| `useDiscussionStore` | 74 | 讨论列表 CRUD + 当前讨论 detail |
| `usePanelStore` | 134 | 嘉宾阵容生成/编辑/确认流程 + 脏检测 |
| `useStudioStore` | 243 | 演播厅实时状态 — Transcript/Streaming/共识/分歧/专家状态/WS事件处理 |
| `useToastStore` | 30 | 全局 Toast 通知 |

---

## 6. API 与通信

### REST API (2 模块)

| 模块 | 端点数 | 封装 |
|------|--------|------|
| `api/discussions.ts` | 8 | 讨论 CRUD + 控制操作 |
| `api/panel.ts` | 2 | 嘉宾生成 + 阵容确认 |

### WebSocket (1 模块)

| 模块 | 功能 |
|------|------|
| `ws/wsClient.ts` | 连接管理 + 自动重连(指数退避×3) + 事件分发 |

**支持 6 种 S→C 事件**: `expert_status` / `utterance_token` / `utterance_complete` / `consensus_update` / `discussion_paused|resumed|ended`  
**支持 4 种 C→S 命令**: `advance` / `pause` / `resume` / `end`

---

## 7. 设计系统

| 属性 | 值 |
|------|----|
| 设计源 | UI UX Pro Max v2.5 / HTML 原型 |
| 风格 | Dark Mode OLED |
| 背景 | `#020617` (slate-950) |
| 卡片 | `#1E293B` (slate-800) |
| 主色调 | `#22C55E` (green-500) |
| 字体 | Fira Code (heading) + Fira Sans (body) |
| 圆角 | 6px / 10px / 16px |
| Z-Index | -1 / 0 / 20 / 30 / 40 / 50 |
| 断点 | lg(1400px) / md(800px) / sm(<800px) |

---

## 8. 与 API_CONTRACT.md 对齐

| 契约项 | 对齐状态 |
|--------|----------|
| `POST /api/discussions` | ✅ CreateDiscussionRequest → createDiscussion() |
| `GET /api/discussions?status=live` | ✅ fetchDiscussions('live') |
| `GET /api/discussions/{id}` | ✅ fetchDiscussionDetail() |
| `POST /.../panel/generate` | ✅ generatePanel() |
| `PUT /.../panel` | ✅ confirmPanel() |
| `POST /.../start/pause/resume/next/end` | ✅ 全部封装, StudioPage 通过 WS 发送 |
| `GET /.../report` | ✅ fetchDiscussionReport() (ReportPage 通过 detail 替代) |
| `WS /ws/discussions/{id}` | ✅ StudioWebSocket 类 |
| WS `expert_status` | ✅ StudioStore.handleExpertStatus → ExpertCard 更新 |
| WS `utterance_token` | ✅ StudioStore.handleUtteranceToken → StreamingText |
| WS `utterance_complete` | ✅ StudioStore.handleUtteranceComplete → UtteranceItem |
| WS `consensus_update` | ✅ StudioStore.handleConsensusUpdate → ConsensusItem |
| WS `discussion_paused|resumed|ended` | ✅ StudioStore 完整处理 |
| 错误码 40001/40002/40301/... | ✅ API interceptor 统一捕获 + Toast |
| Session ID | ✅ localStorage UUID v4, X-Session-Id 头自动注入 |

---

## 9. 运行方案

### 前置条件

- Node.js >= 18
- npm >= 9

### 安装与启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖 (首次)
npm install

# 3. 开发模式启动
npm run dev
# → http://localhost:5173

# 4. 生产构建
npm run build
# → dist/ 目录，静态部署

# 5. 预览生产构建
npm run preview
# → http://localhost:4173
```

### 后端依赖

前端开发模式依赖后端提供 API。启动后端后，Vite 代理会自动转发：

```
http://localhost:5173/api/*       → http://localhost:8000/api/*
http://localhost:5173/ws/*        → ws://localhost:8000/ws/*
```

**后端启动** (后续开发):

```bash
cd backend
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 完整开发链路

```
Terminal 1: cd backend  && uv run uvicorn app.main:app --reload
Terminal 2: cd frontend && npm run dev
Browser:    http://localhost:5173
```

### 纯前端演示 (无需后端)

HTML 原型文件可直接在浏览器打开，无需任何构建：

```bash
# 双击或在浏览器中打开:
frontend/prototype/home.html             # 首页原型
frontend/prototype/ai-panel-studio.html  # 演播厅原型
```
