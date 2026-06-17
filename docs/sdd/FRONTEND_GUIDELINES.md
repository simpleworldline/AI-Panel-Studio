# AI Panel Studio — 前端工程规范

> **阶段**: SDD  
> **日期**: 2026-06-17

---

## 1. 目录结构

```
frontend/
├── public/
│   └── favicon.svg
├── src/
│   ├── api/                          # API 通信层
│   │   ├── client.ts                 # Axios 实例 + 拦截器
│   │   ├── discussions.ts            # 讨论 API 封装
│   │   └── panel.ts                  # 嘉宾 API 封装
│   │
│   ├── ws/                           # WebSocket 通信层
│   │   ├── wsClient.ts               # WebSocket 连接管理（重连/心跳）
│   │   └── useWebSocket.ts           # React Hook 封装
│   │
│   ├── components/                   # 通用 UI 组件
│   │   ├── ui/                       # 基础 UI 元件
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Toast.tsx
│   │   │   ├── Spinner.tsx
│   │   │   ├── Badge.tsx
│   │   │   └── ColorPicker.tsx
│   │   ├── DiscussionCard.tsx        # 讨论卡片
│   │   ├── MemberCard.tsx            # 嘉宾卡片
│   │   ├── ExpertStatusPanel.tsx     # 专家状态面板（含小窗）
│   │   ├── TranscriptView.tsx        # Transcript 展示区
│   │   ├── ConsensusPanel.tsx        # 共识/分歧展示区
│   │   ├── ControlBar.tsx            # 讨论控制栏
│   │   └── StreamingText.tsx         # 流式打字机文本组件
│   │
│   ├── features/                     # 功能模块（页面级拆分）
│   │   ├── create/                   # 创建讨论
│   │   │   ├── CreateDiscussionPage.tsx
│   │   │   └── TopicForm.tsx
│   │   ├── panel/                    # 嘉宾编辑
│   │   │   ├── PanelSetupPage.tsx
│   │   │   ├── HostEditor.tsx
│   │   │   ├── ExpertEditor.tsx
│   │   │   └── MemberEditModal.tsx
│   │   ├── studio/                   # 演播厅
│   │   │   ├── StudioPage.tsx
│   │   │   ├── StudioLayout.tsx      # 响应式三栏/两栏/单栏布局
│   │   │   └── hooks/
│   │   │       ├── useStudioWebSocket.ts
│   │   │       ├── useTranscript.ts
│   │   │       └── useConsensus.ts
│   │   └── report/                   # 讨论报告
│   │       └── ReportPage.tsx
│   │
│   ├── hooks/                        # 全局自定义 Hooks
│   │   ├── useDiscussions.ts
│   │   └── useSession.ts
│   │
│   ├── store/                        # Zustand 状态管理
│   │   ├── useDiscussionStore.ts     # 讨论列表 + 当前讨论
│   │   ├── usePanelStore.ts          # 嘉宾阵容编辑状态
│   │   └── useStudioStore.ts         # 演播厅实时状态（WS驱动）
│   │
│   ├── types/                        # TypeScript 类型定义
│   │   ├── discussion.ts             # Discussion / PanelMember / Utterance
│   │   ├── consensus.ts              # ConsensusDisagreement
│   │   ├── expert.ts                 # ExpertStatus
│   │   └── ws.ts                     # WebSocket 事件类型
│   │
│   ├── utils/                        # 工具函数
│   │   ├── format.ts                 # 日期/文本格式化
│   │   └── color.ts                  # 颜色处理
│   │
│   ├── layouts/
│   │   └── AppLayout.tsx             # 全局布局（Header + 内容）
│   │
│   ├── pages/                        # 路由入口（薄层，组合 features）
│   │   ├── HomePage.tsx
│   │   ├── CreateDiscussionPage.tsx
│   │   ├── PanelSetupPage.tsx
│   │   ├── StudioPage.tsx
│   │   └── ReportPage.tsx
│   │
│   ├── App.tsx                       # 路由定义
│   ├── main.tsx                      # 入口
│   └── index.css                     # Tailwind 入口 + 全局样式变量
│
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
└── .eslintrc.cjs
```

---

## 2. 路由规范

### 2.1 路由定义

```typescript
// src/App.tsx
const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "create", element: <CreateDiscussionPage /> },
      { path: "create/:discussionId/panel", element: <PanelSetupPage /> },
      { path: "studio/:discussionId", element: <StudioPage /> },
      { path: "report/:discussionId", element: <ReportPage /> },
    ],
  },
]);
```

### 2.2 路由守卫

| 规则 | 处理 |
|------|------|
| `/studio/:id` 讨论不存在 | 重定向到 `/`，Toast 提示 |
| `/studio/:id` 讨论已结束 | 重定向到 `/report/:id` |
| `/create/:id/panel` 讨论不存在 | 重定向到 `/` |
| `/report/:id` 讨论进行中 | 正常显示当前进度快照 |

---

## 3. 组件规范

### 3.1 组件分层原则

```
pages/          → 路由入口，仅组合 features，不包含业务逻辑
features/       → 功能页面核心逻辑，包含 hooks、局部状态
components/     → 可跨页面复用的纯 UI 组件，通过 props 驱动
components/ui/  → 无业务语义的原子/分子组件（Button, Modal, etc.）
```

### 3.2 组件命名

- 文件名与组件名一致：PascalCase
- Hook 以 `use` 开头：`useTranscript.ts`
- 类型文件以实体名命名：`discussion.ts`
- Store 以 `use` 开头：`useDiscussionStore.ts`

### 3.3 Props 类型

```typescript
// 任何组件必须显式声明 Props 类型
interface ExpertStatusPanelProps {
  members: PanelMember[];
  statuses: Map<string, ExpertStatus>;
  className?: string;
}
```

---

## 4. 状态管理规范

### 4.1 Zustand Store 划分

| Store | 职责 | 持久化 |
|-------|------|--------|
| `useDiscussionStore` | 讨论列表、当前选中讨论详情 | 否 |
| `usePanelStore` | 嘉宾阵容编辑态（生成/编辑/确认） | 否 |
| `useStudioStore` | 演播厅实时状态（Transcript/共识/分歧/专家状态） | 否 |

### 4.2 Studio Store 设计（WebSocket 驱动）

```typescript
interface StudioState {
  // 讨论基础信息
  discussionId: string;
  status: 'live' | 'paused' | 'ended';

  // Transcript
  utterances: Utterance[];
  streamingUtterance: StreamingUtterance | null;  // 当前正在流式输出的发言

  // 共识与分歧
  consensusItems: ConsensusRecord[];
  disagreementItems: ConsensusRecord[];

  // 专家状态
  expertStatuses: Map<string, ExpertStatus>;

  // 操作方法
  appendToken: (utteranceId: string, token: string, isLast: boolean) => void;
  completeUtterance: (utterance: Utterance) => void;
  updateExpertStatus: (status: ExpertStatusUpdate) => void;
  upsertConsensus: (record: ConsensusRecord) => void;
  setDiscussionStatus: (status: string) => void;
  reset: () => void;
}
```

---

## 5. WebSocket 使用规范

### 5.1 连接管理 Hook

```typescript
// src/ws/useWebSocket.ts
function useStudioWebSocket(discussionId: string) {
  // 1. 建立连接：ws://host/ws/discussions/{id}?session_id=xxx
  // 2. 自动重连：指数退避，最大 3 次
  // 3. 心跳检测：每 30s 发送 ping
  // 4. 事件分发：根据 type 调用 Store 对应方法
  // 5. 连接状态：connected / reconnecting / disconnected
  // 6. 组件卸载时自动关闭连接
}
```

### 5.2 事件处理映射

```typescript
const EVENT_HANDLERS = {
  expert_status: (data) => store.updateExpertStatus(data),
  utterance_token: (data) => store.appendToken(data.utterance_id, data.token, data.is_last),
  utterance_complete: (data) => store.completeUtterance(data),
  consensus_update: (data) => store.upsertConsensus(data.record),
  discussion_paused: () => store.setDiscussionStatus('paused'),
  discussion_resumed: () => store.setDiscussionStatus('live'),
  discussion_ended: (data) => store.setDiscussionStatus('ended'),
};
```

### 5.3 发送控制指令

```typescript
function sendCommand(ws: WebSocket, type: 'advance' | 'pause' | 'resume' | 'end') {
  ws.send(JSON.stringify({ type }));
}
```

---

## 6. 样式规范

### 6.1 Tailwind CSS 配置

```javascript
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        studio: {
          bg: '#0F1117',       // 演播厅深色背景
          card: '#1A1D2E',     // 卡片背景
          border: '#2A2D3E',   // 边框
          gold: '#F0C060',     // 主持人强调色
        },
        consensus: {
          green: '#34D399',    // 共识绿
          orange: '#FB923C',   // 分歧橙
        },
      },
    },
  },
};
```

### 6.2 响应式断点策略

```
lg: '1024px'   → ≥1400px 实际使用自定义 min-width
md: '768px'    → 800-1399px
sm: '640px'    → <800px
```

使用 Tailwind 前缀: `lg:grid-cols-3 md:grid-cols-2 sm:grid-cols-1`

---

## 7. API 调用规范

### 7.1 封装模式

```typescript
// src/api/client.ts
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// 自动附加 Session ID
apiClient.interceptors.request.use((config) => {
  config.headers['X-Session-Id'] = getSessionId();
  return config;
});

// 统一错误处理
apiClient.interceptors.response.use(
  (res) => res.data,
  (err) => {
    toast.error(err.response?.data?.message || '网络错误');
    return Promise.reject(err);
  }
);
```

### 7.2 类型安全

所有 API 调用必须定义响应类型，使用 TypeScript 泛型：

```typescript
// src/api/discussions.ts
export async function getDiscussions(params: DiscussionListParams) {
  return apiClient.get<ApiResponse<PaginatedList<Discussion>>>('/discussions', { params });
}
```
