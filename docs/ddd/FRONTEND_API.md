# AI Panel Studio — 前端接口文档

> **阶段**: DDD  
> **日期**: 2026-06-18  

---

## 1. 技术层总览

```
┌─────────────────────────────────────────────────┐
│                  Pages (路由入口)                 │
│  HomePage / CreateDiscussion / PanelSetup        │
│  StudioPage / ReportPage                        │
├─────────────────────────────────────────────────┤
│          Store (Zustand 状态管理)                 │
│  useDiscussionStore / usePanelStore              │
│  useStudioStore / useToastStore                 │
├──────────────────┬──────────────────────────────┤
│   API Layer      │      WebSocket Layer         │
│   (Axios)        │      (原生 WebSocket)         │
│   client.ts      │      wsClient.ts             │
│   discussions.ts │                              │
│   panel.ts       │                              │
├──────────────────┴──────────────────────────────┤
│          Utils (工具层)                          │
│  transform.ts / format.ts / session.ts /        │
│  color.ts                                       │
├─────────────────────────────────────────────────┤
│          Types (TypeScript 类型定义)             │
│  discussion.ts / expert.ts / consensus.ts /     │
│  ws.ts                                          │
└─────────────────────────────────────────────────┘
```

---

## 2. HTTP API 层

### 2.1 Axios 客户端 (`api/client.ts`)

**实例配置：**

| 配置项 | 值 |
|--------|-----|
| `baseURL` | `/api` |
| `timeout` | 30000ms |
| `Content-Type` | `application/json` |

**请求拦截器：**

- 自动附加 `X-Session-Id` 请求头（从 `localStorage` 读取或生成 UUID）
- 请求体 `camelCase → snake_case` 自动转换

**响应拦截器：**

- 响应体 `snake_case → camelCase` 自动转换
- 统一错误解包：`{ message, code, detail }`

**导出：**

```typescript
export const apiClient: AxiosInstance
```

---

### 2.2 讨论 API (`api/discussions.ts`)

#### `fetchDiscussions(status?, page?, pageSize?)`

获取讨论列表。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `status` | `'live' \| 'ended'` | — | 可选，按状态筛选 |
| `page` | `number` | `1` | 页码 |
| `pageSize` | `number` | `50` | 每页数量 |

**返回：** `ApiResponse<PaginatedList<DiscussionSummary>>`

**对应端点：** `GET /api/discussions`

---

#### `createDiscussion(data)`

创建新讨论。

| 参数 | 类型 | 说明 |
|------|------|------|
| `data.topic` | `string` | 话题，1-200字 |
| `data.expertCount` | `number` | 嘉宾人数，2-8 |
| `data.maxRounds` | `number \| null` | 最大轮次，null=不限 |

**返回：** `ApiResponse<Discussion>`

**对应端点：** `POST /api/discussions`

---

#### `fetchDiscussionDetail(id)`

获取讨论详情（含 transcript、panel、consensus）。

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | `string` | 讨论 UUID |

**返回：** `ApiResponse<DiscussionDetail>`

**对应端点：** `GET /api/discussions/{id}`

---

#### `startDiscussion(id)` / `pauseDiscussion(id)` / `resumeDiscussion(id)` / `advanceDiscussion(id)` / `endDiscussion(id)`

讨论控制操作。

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | `string` | 讨论 UUID |

**对应端点：**

| 函数 | 端点 |
|------|------|
| `startDiscussion` | `POST /api/discussions/{id}/start` |
| `pauseDiscussion` | `POST /api/discussions/{id}/pause` |
| `resumeDiscussion` | `POST /api/discussions/{id}/resume` |
| `advanceDiscussion` | `POST /api/discussions/{id}/next` |
| `endDiscussion` | `POST /api/discussions/{id}/end` |

---

#### `fetchDiscussionReport(id)`

获取讨论总结报告。

| 参数 | 类型 | 说明 |
|------|------|------|
| `id` | `string` | 讨论 UUID |

**返回：** `ApiResponse<DiscussionReport>`

**对应端点：** `GET /api/discussions/{id}/report`

---

### 2.3 嘉宾 API (`api/panel.ts`)

#### `generatePanel(discussionId, data)`

调用 LLM 生成嘉宾阵容建议。

| 参数 | 类型 | 说明 |
|------|------|------|
| `discussionId` | `string` | 讨论 UUID |
| `data.regenerateMemberId` | `string \| null` | 单体重生时指定成员 ID，null=全量生成 |

**返回：** `ApiResponse<PanelGenerateResponse>`

**对应端点：** `POST /api/discussions/{id}/panel/generate`

---

#### `confirmPanel(discussionId, data)`

编辑并确认嘉宾阵容。

| 参数 | 类型 | 说明 |
|------|------|------|
| `discussionId` | `string` | 讨论 UUID |
| `data.host` | `PanelMemberDraft` | 主持人信息 |
| `data.experts` | `PanelMemberDraft[]` | 嘉宾列表 |

**返回：** `ApiResponse<{ discussionId, panelConfirmed, members }>`

**对应端点：** `PUT /api/discussions/{id}/panel`

---

### 2.4 通用响应格式

```typescript
interface ApiResponse<T> {
  code: number;       // 200=成功, 201=创建成功, 4xx/5xx=错误
  data: T;            // 业务数据
  message: string;    // 提示信息
  detail?: string;    // 错误详情（可选）
}

interface PaginatedList<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
}
```

**错误解包格式（拦截器统一抛出）：**

```typescript
{ message: string; code: number; detail: string }
```

---

## 3. WebSocket 层

### 3.1 客户端类 (`ws/wsClient.ts`)

**类名：** `StudioWebSocket`

**构造：**

```typescript
new StudioWebSocket(
  discussionId: string,
  sessionId: string,
  handler: (event: WsServerEvent) => void
)
```

**方法：**

| 方法 | 说明 |
|------|------|
| `connect()` | 建立 WebSocket 连接 |
| `send(command)` | 发送 C→S 控制指令 |
| `close()` | 关闭连接并停止重连 |

**连接地址：**
```
ws://{host}/ws/discussions/{discussionId}?session_id={sessionId}
```

**重连策略：**
- 指数退避：1s → 2s → 4s
- 最大重连次数：3 次
- `close()` 被调用后永不重连

**数据转换：**
- 接收：`snake_case → camelCase`（后端 Python 输出 snake_case）
- 发送：`camelCase → snakeCase`（后端 Python 接收 snake_case）

---

### 3.2 服务端 → 客户端事件

#### `expert_status` — 专家状态变更

```typescript
{
  type: 'expert_status';
  data: {
    memberId: string;
    memberName: string;
    memberColor: string;       // hex 颜色
    status: 'idle' | 'preparing' | 'speaking';
    focusSummary: string | null; // 当前关注点摘要
    desireValue: number;         // 发言欲望值 0-1
    timestamp: string;           // ISO 8601
  };
}
```

---

#### `utterance_token` — 流式发言 Token

```typescript
{
  type: 'utterance_token';
  data: {
    utteranceId: string;
    memberId: string;
    memberName: string;
    memberTitle: string;
    memberColor: string;
    token: string;               // 增量文本片段
    sequenceNum: number;
    roundNum: number;
    isFirst: boolean;            // 该发言的首个 token
    isLast: boolean;             // 该发言的最后一个 token
  };
}
```

**前端处理：** 首次 token 创建 `StreamingUtterance`，后续追加文本到 `accumulatedText`。`isLast` 时标记 `isStreaming=false`。

---

#### `utterance_complete` — 发言完成

```typescript
{
  type: 'utterance_complete';
  data: {
    utteranceId: string;
    memberId: string;
    memberName: string;
    memberTitle: string;
    memberColor: string;
    content: string;             // 完整发言文本
    utteranceType: 'opening' | 'statement' | 'question' | 'reply' | 'summary';
    sequenceNum: number;
    roundNum: number;
    createdAt: string;           // ISO 8601
  };
}
```

**前端处理：** 清除 `streaming`，追加到 `utterances[]` 数组。

---

#### `consensus_update` — 共识/分歧更新

```typescript
{
  type: 'consensus_update';
  data: {
    action: 'created' | 'updated' | 'resolved';
    record: {
      id: string;
      type: 'consensus' | 'disagreement';
      title: string;
      description: string;
      sourceUtteranceIds: string[];
      confidence: number;        // 0-1
      isResolved: boolean;
      roundNum: number;
    };
  };
}
```

---

#### 讨论控制事件

```typescript
// 暂停
{ type: 'discussion_paused'; data: { discussionId: string; timestamp: string } }

// 继续
{ type: 'discussion_resumed'; data: { discussionId: string; timestamp: string } }

// 结束
{ type: 'discussion_ended'; data: {
    discussionId: string;
    endReason: 'user_ended' | 'max_rounds' | 'no_consensus' | 'host_decided';
    totalRounds: number;
    totalUtterances: number;
    endedAt: string;
} }

// 面板状态消息
{ type: 'discussion_control'; data: { action: string; message: string } }

// 初始快照
{ type: 'initial_snapshot'; data: {
    discussionId: string;
    status: string;
    currentRound: number;
    totalUtterances: number;
    transcript: any[];
    consensus: any[];
    disagreements: any[];
} }
```

---

### 3.3 客户端 → 服务端指令

```typescript
type WsClientCommand =
  | { type: 'advance' }   // 手动推进下一轮
  | { type: 'pause' }     // 暂停讨论
  | { type: 'resume' }    // 继续讨论
  | { type: 'end' };      // 强制结束讨论
```

---

## 4. 状态管理 (Zustand Stores)

### 4.1 `useDiscussionStore`

**职责：** 讨论列表 + 当前讨论详情

| 状态 | 类型 | 说明 |
|------|------|------|
| `discussions` | `DiscussionSummary[]` | 列表数据 |
| `listLoading` | `boolean` | 列表加载中 |
| `listError` | `string \| null` | 列表错误 |
| `activeTab` | `'live' \| 'ended'` | 当前 Tab |
| `currentDiscussion` | `DiscussionDetail \| null` | 当前详情 |
| `detailLoading` | `boolean` | 详情加载中 |
| `detailError` | `string \| null` | 详情错误 |

| 方法 | 说明 |
|------|------|
| `fetchList(status?)` | 拉取列表 |
| `fetchDetail(id)` | 拉取详情 |
| `clearCurrent()` | 清除当前详情 |
| `setActiveTab(tab)` | 切换 Tab |

---

### 4.2 `usePanelStore`

**职责：** 嘉宾阵容编辑态

| 状态 | 类型 | 说明 |
|------|------|------|
| `discussionId` | `string` | 讨论 UUID |
| `expertCount` | `number` | 嘉宾数量 |
| `host` | `PanelMemberDraft \| null` | 主持人草稿 |
| `experts` | `PanelMemberDraft[]` | 嘉宾草稿列表 |
| `generating` | `boolean` | 生成中 |
| `generateError` | `string \| null` | 生成错误 |
| `confirming` | `boolean` | 确认中 |
| `confirmError` | `string \| null` | 确认错误 |

| 方法 | 说明 |
|------|------|
| `init(discussionId, expertCount)` | 初始化 |
| `generate(discussionId)` | LLM 全量生成 |
| `regenerateOne(discussionId, index)` | 单体重新生成 |
| `regenerateAll(discussionId)` | 全体重新生成 |
| `updateHost(data)` | 编辑主持人 |
| `updateExpert(index, data)` | 编辑某位嘉宾 |
| `confirm(discussionId)` | 确认阵容 → 返回 members |
| `reset()` | 重置 |

---

### 4.3 `useStudioStore`

**职责：** 演播厅实时状态（WebSocket 驱动）

| 状态 | 类型 | 说明 |
|------|------|------|
| `discussionId` | `string` | 讨论 UUID |
| `topic` | `string` | 讨论话题 |
| `status` | `'live' \| 'paused' \| 'ended'` | 讨论状态 |
| `isCreator` | `boolean` | 是否创建者 |
| `currentRound` | `number` | 当前轮次 |
| `maxRounds` | `number \| null` | 最大轮次 |
| `totalUtterances` | `number` | 发言总数 |
| `members` | `PanelMember[]` | 嘉宾列表 |
| `utterances` | `UtteranceDisplay[]` | 已完成的发言 |
| `streaming` | `StreamingUtterance \| null` | 当前流式发言 |
| `consensusItems` | `ConsensusRecord[]` | 共识列表 |
| `disagreementItems` | `ConsensusRecord[]` | 分歧列表 |
| `expertStatuses` | `Record<string, ExpertStatus>` | 专家状态映射 |
| `wsStatus` | `'connecting' \| 'connected' \| 'reconnecting' \| 'disconnected'` | WS 连接状态 |

| WS Handler | 对应事件 |
|------------|----------|
| `handleExpertStatus(data)` | `expert_status` |
| `handleUtteranceToken(data)` | `utterance_token` |
| `handleUtteranceComplete(data)` | `utterance_complete` |
| `handleConsensusUpdate(data)` | `consensus_update` |
| `handleInitialSnapshot(data)` | `initial_snapshot` |
| `handleDiscussionPaused()` | `discussion_paused` |
| `handleDiscussionResumed()` | `discussion_resumed` |
| `handleDiscussionEnded()` | `discussion_ended` |

---

### 4.4 `useToastStore`

**职责：** 全局 Toast 通知

| 状态/方法 | 类型 | 说明 |
|-----------|------|------|
| `toasts` | `Toast[]` | 当前显示的 Toast 列表 |
| `addToast(t)` | `(t: { type, message }) => void` | 添加 Toast（4s 自动消失） |
| `removeToast(id)` | `(id: string) => void` | 手动移除 |

---

## 5. 工具函数

### 5.1 `utils/session.ts`

| 函数 | 说明 |
|------|------|
| `getSessionId()` | 获取或创建 Session ID（存 `localStorage`） |

### 5.2 `utils/transform.ts`

| 函数 | 说明 |
|------|------|
| `keysToCamel<T>(obj)` | `snake_case → camelCase` 递归转换 |
| `keysToSnake<T>(obj)` | `camelCase → snake_case` 递归转换 |

### 5.3 `utils/format.ts`

| 函数 | 说明 |
|------|------|
| `formatTime(iso)` | ISO → `HH:mm` |
| `formatDate(iso)` | ISO → `YYYY-MM-DD` |
| `formatRelative(iso)` | ISO → `刚刚` / `5 分钟前` / `3 天前` |
| `truncateText(text, max)` | 文本截断 |
| `statusLabel(status)` | `live` → `进行中` 等 |
| `utteranceTypeLabel(type)` | `statement` → `发言` 等 |
| `expertStatusLabel(status)` | `speaking` → `发言中` 等 |

### 5.4 `utils/color.ts`

| 导出 | 类型 | 说明 |
|------|------|------|
| `EXPERT_COLORS` | `string[]` | 8 种预设专家颜色 |
| `EXPERT_COLOR_LABELS` | `string[]` | 颜色中文名 |
| `isValidHex(color)` | 函数 | hex 格式校验 |
| `getColorStyles(hex)` | 函数 | 返回 `{ bg, text, ring, dot }` |

---

## 6. TypeScript 类型定义

### 6.1 `types/discussion.ts`

| 类型 | 说明 |
|------|------|
| `DiscussionStatus` | `'pending' \| 'live' \| 'paused' \| 'ended'` |
| `MemberRole` | `'host' \| 'expert'` |
| `UtteranceType` | `'opening' \| 'statement' \| 'question' \| 'reply' \| 'summary'` |
| `PanelMember` | 嘉宾完整信息 |
| `Utterance` | 发言完整信息 |
| `ConsensusRecord` | 共识/分歧记录 |
| `Discussion` | 讨论基础信息 |
| `DiscussionSummary` | 讨论列表项 |
| `DiscussionDetail` | 讨论详情 |
| `DiscussionReport` | 讨论报告 |
| `ApiResponse<T>` | 通用 API 响应 |
| `PaginatedList<T>` | 分页列表 |

### 6.2 `types/expert.ts`

| 类型 | 说明 |
|------|------|
| `ExpertStatusKind` | `'idle' \| 'preparing' \| 'speaking'` |
| `ExpertStatus` | 专家实时状态 |

### 6.3 `types/consensus.ts`

| 类型 | 说明 |
|------|------|
| `ConsensusType` | `'consensus' \| 'disagreement'` |
| `ConsensusItemDisplay` | 共识/分歧展示项 |

### 6.4 `types/ws.ts`

| 类型 | 说明 |
|------|------|
| `WsExpertStatus` | 专家状态事件 |
| `WsUtteranceToken` | 流式 Token 事件 |
| `WsUtteranceComplete` | 发言完成事件 |
| `WsConsensusUpdate` | 共识更新事件 |
| `WsDiscussionPaused` | 暂停事件 |
| `WsDiscussionResumed` | 继续事件 |
| `WsDiscussionEnded` | 结束事件 |
| `WsDiscussionControl` | 面板消息事件 |
| `WsInitialSnapshot` | 初始快照事件 |
| `WsServerEvent` | 所有 S→C 事件联合类型 |
| `WsClientCommand` | 所有 C→S 指令联合类型 |

---

## 7. 数据流转图

```
用户创建讨论
     │
     ▼
CreateDiscussionPage → createDiscussion() → POST /api/discussions
     │
     ▼
PanelSetupPage → generatePanel() → POST /api/.../panel/generate
     │  (用户编辑嘉宾)
     ▼
PanelSetupPage → confirmPanel() → PUT /api/.../panel
     │
     ▼
StudioPage → init store → connect WebSocket
     │
     ├─► WS: expert_status      → useStudioStore.handleExpertStatus
     ├─► WS: utterance_token    → useStudioStore.handleUtteranceToken
     ├─► WS: utterance_complete → useStudioStore.handleUtteranceComplete
     ├─► WS: consensus_update   → useStudioStore.handleConsensusUpdate
     ├─► WS: discussion_ended   → useStudioStore.handleDiscussionEnded
     │
     └─► 每 3s 轮询 GET /api/discussions/{id} (兜底)
```

---

## 8. 错误处理策略

| 层级 | 策略 |
|------|------|
| Axios 拦截器 | 统一解包 `{ message, code, detail }` |
| API 函数 | 透传拦截器处理后的错误 |
| Store 方法 | `try/catch` 后设置 `xxxError` 状态 |
| 页面组件 | 展示错误状态 + 重试按钮 |
| WebSocket | `onerror` → `onclose` → 自动重连（3次） |
| Toast | 操作成功/失败即时通知，4s 自动消失 |
