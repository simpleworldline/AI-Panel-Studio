# AI Panel Studio — 状态流转文档

> **阶段**: DDD  
> **日期**: 2026-06-17  
> **状态管理**: Zustand 4 (3 Store 划分)  
> **来源**: SDD FRONTEND_GUIDELINES.md §4 + APP_FLOW.md + HTML 原型交互

---

## 1. Zustand Store 完整定义

### 1.1 `useDiscussionStore` — 讨论列表与当前讨论

**作用域**: HomePage, CreateDiscussionPage, 路由守卫

```typescript
interface DiscussionSummary {
  id: string;
  topic: string;
  expertCount: number;
  status: 'pending' | 'live' | 'paused' | 'ended';
  currentRound: number;
  createdAt: string;
  memberPreview: { name: string; role: 'host' | 'expert'; color: string }[];
}

interface DiscussionDetail extends DiscussionSummary {
  maxRounds: number | null;
  endedAt: string | null;
  creatorSessionId: string;
  panel: PanelMember[];
  transcript: Utterance[];
  consensus: ConsensusRecord[];
  disagreements: ConsensusRecord[];
}

// ── State ──
interface DiscussionStoreState {
  // 列表
  liveDiscussions: DiscussionSummary[];
  endedDiscussions: DiscussionSummary[];
  listLoading: boolean;
  listError: string | null;

  // 当前讨论详情
  currentDiscussion: DiscussionDetail | null;
  detailLoading: boolean;
  detailError: string | null;

  // ── Actions ──
  fetchList: (status?: 'live' | 'ended') => Promise<void>;
  fetchDetail: (discussionId: string) => Promise<void>;
  createDiscussion: (data: CreateDiscussionRequest) => Promise<string>; // returns discussionId
  clearCurrent: () => void;
}
```

**生命周期**: 页面级, 不持久化。离开演播厅/报告页时调用 `clearCurrent()`。

---

### 1.2 `usePanelStore` — 嘉宾阵容编辑

**作用域**: PanelSetupPage

```typescript
// ── State ──
interface PanelStoreState {
  discussionId: string | null;

  // 编辑数据
  host: PanelMemberEditable | null;
  experts: PanelMemberEditable[];

  // 流程状态
  generatePhase: 'idle' | 'loading' | 'success' | 'error';
  generateError: string | null;
  confirmPhase: 'idle' | 'loading' | 'success' | 'error';
  confirmError: string | null;

  // 是否有未保存的修改
  isDirty: boolean;

  // ── Actions ──
  initForDiscussion: (discussionId: string) => void;
  generatePanel: (expertCount: number) => Promise<void>;
  regenerateMember: (memberId: string) => Promise<void>;
  regenerateAll: (expertCount: number) => Promise<void>;

  // 编辑操作
  updateHost: (field: keyof PanelMemberEditable, value: string) => void;
  updateExpert: (expertId: string, field: keyof PanelMemberEditable, value: string) => void;

  // 确认
  confirmPanel: () => Promise<void>;

  // 重置
  reset: () => void;
}
```

**脏检测**: 任意 `update*` 调用后 `isDirty = true`。浏览器关闭/跳转前若 `isDirty && !confirmed` 弹出确认。

---

### 1.3 `useStudioStore` — 演播厅实时状态 (WebSocket 驱动)

**作用域**: StudioPage (仅 /studio/:id 路由激活时实例化)

```typescript
// ── 类型 ──
interface StreamingUtterance {
  utteranceId: string;
  memberId: string;
  memberName: string;
  memberTitle: string;
  memberColor: string;
  accumulatedText: string;           // 逐 token 累积
  isStreaming: boolean;
}

interface ExpertStatus {
  memberId: string;
  status: 'idle' | 'preparing' | 'speaking';
  focusSummary: string | null;
  desireValue: number;               // 0.00 - 1.00
  timestamp: string;
}

// ── State ──
interface StudioStoreState {
  discussionId: string;
  topic: string;
  status: 'live' | 'paused' | 'ended';
  isCreator: boolean;
  currentRound: number;
  maxRounds: number | null;
  totalUtterances: number;

  // 嘉宾阵容 (静态)
  members: PanelMember[];

  // Transcript
  utterances: Utterance[];
  streaming: StreamingUtterance | null;

  // 共识与分歧
  consensusItems: ConsensusRecord[];
  disagreementItems: ConsensusRecord[];

  // 专家状态
  expertStatuses: Record<string, ExpertStatus>;  // key = memberId

  // WebSocket 连接状态
  wsStatus: 'connecting' | 'connected' | 'reconnecting' | 'disconnected';
  wsReconnectAttempt: number;

  // ── Actions ──

  // 初始化
  init: (detail: DiscussionDetail, isCreator: boolean) => void;
  reset: () => void;

  // WebSocket 事件处理方法
  handleExpertStatus: (data: WsExpertStatus) => void;
  handleUtteranceToken: (data: WsUtteranceToken) => void;
  handleUtteranceComplete: (data: WsUtteranceComplete) => void;
  handleConsensusUpdate: (data: WsConsensusUpdate) => void;
  handleDiscussionPaused: () => void;
  handleDiscussionResumed: () => void;
  handleDiscussionEnded: (data: WsDiscussionEnded) => void;

  // WebSocket 连接状态
  setWsStatus: (status: StudioStoreState['wsStatus']) => void;
}
```

---

## 2. 页面状态机

### 2.1 HomePage 状态机

```
              ┌────────────┐
              │   初始化     │
              │ (首次挂载)   │
              └──────┬─────┘
                     │
                     ▼
            fetchDiscussionList()
                     │
           ┌─────────┴─────────┐
           ▼                   ▼
    ┌──────────┐        ┌──────────┐
    │ 加载成功  │        │ 加载失败  │
    │ listLoaded│        │ listError │
    └────┬─────┘        └────┬─────┘
         │                   │
         ▼                   ▼
    ┌──────────┐        ├── Toast 错误提示
    │Tab: live  │        └── 手动重试 (pull-to-refresh 或按钮)
    │Tab: ended │
    └────┬─────┘
         │
    ┌────┴────┐
    ▼         ▼
┌──────┐ ┌──────┐
│有数据 │ │空数据 │
│Card[]│ │Empty │
│      │ │State │
└──┬───┘ └──────┘
   │
   ├── 点击 "进行中" Card → navigate(`/studio/${id}`)
   ├── 点击 "已结束" Card → navigate(`/report/${id}`)
   └── 点击 "发起新讨论" → navigate('/create') 或 openCreateModal()
```

**Tab 状态**: `activeTab: 'live' | 'ended'` — URL search param `?tab=live|ended`, 切换时仅过滤客户端数据, 不做额外请求。

---

### 2.2 CreateDiscussionPage 状态机

```
┌──────────────┐
│   idle        │  表单为空
│  (初始态)      │
└──────┬───────┘
       │
       ├── 话题为空 → button[disabled], hint "请输入讨论话题"
       ├── 话题 1-200字 → button[enabled]
       └── 话题 >200字 → input[error], counter 红色
              │
              ▼
       ┌──────────────┐
       │  submitting   │  POST /api/disucssions 进行中
       │  button[loading]│
       │  表单[disabled] │
       └──────┬───────┘
              │
      ┌───────┴───────┐
      ▼               ▼
┌──────────┐    ┌──────────┐
│ success   │    │  error    │
│ 201 创建  │    │ 4xx/5xx   │
│ 跳转 panel│    │ Toast +   │
│           │    │ 回 idle   │
└──────────┘    └──────────┘
```

**表单字段**:
- `topic: string` — 0-200 字
- `expertCount: number` — 2-8
- `maxRounds: number | null` — 0 或 null 表示不限

---

### 2.3 PanelSetupPage 状态机

```
┌───────────────────────────────────────────────────────────────┐
│                          主流程                                │
│                                                                │
│  ┌────────┐   POST /generate   ┌──────────┐  PUT /panel  ┌────┴─────┐
│  │ loading │ ─────────────────→ │ editing   │ ──────────→ │ redirect  │
│  │(spinner)│                    │ (可操作)   │              │ /studio   │
│  └────────┘                    └────┬─────┘              └──────────┘
│                                     │
│                       ┌─────────────┼─────────────┐
│                       ▼             ▼             ▼
│                 ┌──────────┐ ┌───────────┐ ┌──────────┐
│                 │编辑嘉宾卡片│ │ 单体重生    │ │ 全体重生   │
│                 │MemberEdit │ │regenOne() │ │regenAll()│
│                 │  Modal    │ │           │ │          │
│                 └──────────┘ └─────┬─────┘ └────┬─────┘
│                                    │            │
│                            POST /generate  POST /generate
│                           {regenerate_member_id}
│                                    │            │
│                                    ▼            ▼
│                              ┌────────────────────┐
│                              │  loading (局部)     │
│                              │  单个卡片骨架屏      │
│                              └────────┬───────────┘
│                                       │
│                                       ▼ 回到 editing
│                              ┌────────────────────┐
│                              │ 替换/更新对应 Member │
│                              └────────────────────┘
└───────────────────────────────────────────────────────────────┘
```

**编辑 → 脏检测**:
- `isDirty === true` 时离开页面 → `window.confirm("阵容未确认，确定离开？")`
- `confirmPanel()` 成功后 `isDirty = false`

**错误处理**:
- 生成失败 → Toast "嘉宾生成失败，请重试" → 停留在当前态
- 确认失败 → Toast 错误信息 → 仍可编辑重试

---

### 2.4 StudioPage 状态机 (核心)

```
                                ┌──────────────────┐
                                │   进入 StudioPage  │
                                │   (路由匹配)        │
                                └────────┬─────────┘
                                         │
                            ┌────────────┴────────────┐
                            ▼                         ▼
                   GET /api/discussions/:id   权限校验 (creator_session_id)
                            │                         │
                            ▼                         ▼
                    ┌──────────────┐          非创建者 → isCreator=false
                    │ 初始化 Store  │
                    │ init(detail) │
                    └──────┬───────┘
                           │
                           ▼
                   ┌──────────────────┐
                   │ 建立 WebSocket 连接│
                   │ wsStatus=connecting│
                   └──────┬───────────┘
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
        ┌──────────────┐    ┌──────────────────┐
        │  connected    │    │ 连接失败 (3次重试)  │
        │ wsStatus=     │    │ wsStatus=         │
        │  connected    │    │  disconnected     │
        └──────┬───────┘    └────────┬─────────┘
               │                     │
               │                     ▼
               │              ┌────────────┐
               │              │ Toast 错误   │
               │              │ "连接断开..." │
               │              │ 手动刷新页面   │
               │              └────────────┘
               │
    ┌──────────┴───────────┐
    ▼                      ▼
┌────────┐          ┌──────────────┐
│status= │          │ status=      │
│ live   │          │ paused       │
│        │          │              │
│ 事件接收│          │ 事件接收 (暂停)│
│ ┌────┐ │          │ ┌────┐       │
│ │S→C │ │          │ │S→C │       │
│ └────┘ │          │ └────┘       │
│ ┌────┐ │          │              │
│ │C→S │ │          │ 按钮: [继续]   │
│ └────┘ │          │ 按钮: [下一轮]  │
│        │          │ 按钮: [结束]    │
│ 按钮:   │          └──────┬───────┘
│ [暂停]  │                 │
│ [下一轮]│          [resume]┘
│ [结束]  │                 ▼
└───┬────┘          重新进入 live
    │
    ├── [pause] → 发送 C→S pause → 等待 S→C discussion_paused
    ├── [advance] → 发送 C→S advance → 触发下一轮
    ├── [end] → 发送 C→S end → 等待 S→C discussion_ended
    │
    └── 自动结束条件:
        1. currentRound >= maxRounds
        2. roundsWithoutConsensus >= auto_end_threshold
        3. 触发 → discussion_ended
                │
                ▼
        ┌──────────────┐
        │  status=ended │
        │  按钮全部禁用   │
        │  显示总结入口    │
        │  "查看报告" →   │
        │  /report/:id   │
        └──────────────┘
```

---

## 3. 一轮发言的 UI 状态流转 (粒度事件序列)

```
时间轴 t →
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▶

t0: 上一发言刚刚 utterance_complete
    所有 expert status: idle
    streaming: null

t1: S→C expert_status ×N
    专家A: idle → preparing, desire=0.72, focus="正在思考..."
    专家B: idle → preparing, desire=0.85, focus="准备反驳..."
    主持人: idle → preparing, desire=0.81
    专家C: idle (desire 不够, 不进入 preparing)
    
    UI: 
    - ExpertCard A: 状态灯 idle(灰)→preparing(橙呼吸), 关注点文字更新, 欲望条动画到 72
    - ExpertCard B: 状态灯 idle(灰)→preparing(橙呼吸), 欲望条动画到 85
    - ExpertCard 主持人: 状态灯 idle→preparing, 欲望条动画到 81

t2: [Scheduler 选择专家B (desire=0.85 最高)]

t3: S→C expert_status
    专家A: preparing → idle (未被选中)
    主持人: preparing → idle
    专家B: preparing → speaking, focus="正在阐述..."
    
    UI:
    - ExpertCard A: 状态灯橙→灰, 欲望条渐隐
    - ExpertCard B: 状态灯橙→蓝(快速呼吸), 左侧竖线发光 (glow-bar), 关注点更新

t4 ~ t(n-1): S→C utterance_token ×N (逐 token)
    专家B 发言内容逐 token 推送到前端
    
    UI:
    - TranscriptView 底部: <StreamingText /> 逐字追加
    - 光标 ▍ 跟随文本末尾闪烁
    - 自动滚动跟底

tn: S→C utterance_token (is_last: true)
    
    UI:
    - 最后一个 token 追加完毕
    - 光标闪烁 → 即将完成

t(n+1): S→C utterance_complete
    {
      utteranceId, memberId, memberName, memberTitle, memberColor,
      content: "完整发言文本...",
      utteranceType: "statement",
      sequenceNum: 5, roundNum: 2
    }
    
    UI:
    - <StreamingText /> 移除, 光标消失
    - 新增 <UtteranceItem /> (fadeInUp 动画)
    - utterance_count +1

t(n+2): [Observer 分析中] — 前端无需展示, 后端处理

t(n+3): S→C consensus_update (如果发现新共识/分歧)
    
    UI:
    - <ConsensusPanel /> 新增 <ConsensusItem /> (fadeInUp 动画)

t(n+4): S→C expert_status
    专家B: speaking → idle
    
    UI:
    - ExpertCard B: 状态灯蓝→灰, 发光线消失

t(n+5): 如果未结束 → 回到 t1 (等待新一轮触发)
```

---

## 4. 跨页面数据流

```
┌─────────────────────────────────────────────────────────────┐
│                        完整用户旅程                           │
│                                                              │
│  ┌─────────┐      ┌──────────────┐      ┌──────────────────┐ │
│  │ HomePage │      │CreateDiscuss │      │ PanelSetupPage   │ │
│  │          │─────→│ ionPage      │─────→│                  │ │
│  │ 创建讨论  │      │ POST create  │      │ POST generate    │ │
│  │          │      │ → id         │      │ PUT confirm      │ │
│  └─────────┘      └──────────────┘      └────────┬─────────┘ │
│                                                   │           │
│                                            navigate(         │
│                                            `/studio/${id}`)  │
│                                                   │           │
│                                                   ▼           │
│  ┌─────────────┐                        ┌──────────────────┐ │
│  │ ReportPage  │←───────────────────────│   StudioPage     │ │
│  │             │   讨论结束后跳转         │                  │ │
│  │ GET report  │   navigate(            │ WebSocket 实时    │ │
│  │ 只读视图     │   `/report/${id}`)    │ 数据不再经 REST   │ │
│  └─────────────┘                        └──────────────────┘ │
│                                                              │
│  数据传递:                                                   │
│  ─────────                                                   │
│  / → /create         无参数                                   │
│  /create → /panel    discussionId (route param)               │
│  /panel → /studio    discussionId (route param)               │
│  /studio → /report   discussionId (route param)               │
│  / → /studio         discussionId (直接点击列表卡片)            │
│  / → /report         discussionId (直接点击已结束卡片)          │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. WebSocket 事件分发映射

### 5.1 事件 → Store Action

```typescript
// src/ws/useStudioWebSocket.ts
const EVENT_DISPATCH: Record<string, (store: StudioStore, data: any) => void> = {
  'expert_status': (s, d) => s.handleExpertStatus(d),
  'utterance_token': (s, d) => s.handleUtteranceToken(d),
  'utterance_complete': (s, d) => s.handleUtteranceComplete(d),
  'consensus_update': (s, d) => s.handleConsensusUpdate(d),
  'discussion_paused': (s) => s.handleDiscussionPaused(),
  'discussion_resumed': (s) => s.handleDiscussionResumed(),
  'discussion_ended': (s, d) => s.handleDiscussionEnded(d),
  'discussion_control': (s, d) => {
    // 仅 Toast 提示 (如 "已达到预设最大轮次")
    toast.info(d.message);
  },
};
```

### 5.2 各 Action 实现细节

```typescript
// handleUtteranceToken
handleUtteranceToken(data) {
  if (!this.streaming) {
    // 首次 token: 创建 StreamingUtterance
    this.streaming = {
      utteranceId: data.utterance_id,
      memberId: data.member_id,
      memberName: data.member_name,
      memberTitle: data.member_title,
      memberColor: data.member_color,
      accumulatedText: '',
      isStreaming: true,
    };
  }
  // 追加 token
  this.streaming.accumulatedText += data.token;
  if (data.is_last) {
    this.streaming.isStreaming = false;  // 光标消失, 等待 complete
  }
}

// handleUtteranceComplete
handleUtteranceComplete(data) {
  // 将完整发言推入 utterances 列表
  this.utterances.push({
    id: data.utterance_id,
    panelMemberId: data.member_id,
    memberName: data.member_name,
    memberTitle: data.member_title,
    memberColor: data.member_color,
    content: data.content,
    utteranceType: data.utterance_type,
    sequenceNum: data.sequence_num,
    roundNum: data.round_num,
    createdAt: data.created_at,
  });
  this.totalUtterances = data.sequence_num;
  this.currentRound = data.round_num;
  // 清除 streaming
  this.streaming = null;
}

// handleExpertStatus
handleExpertStatus(data) {
  this.expertStatuses[data.member_id] = {
    memberId: data.member_id,
    status: data.status,
    focusSummary: data.focus_summary,
    desireValue: data.desire_value,
    timestamp: data.timestamp,
  };
  // 若 status='speaking', 高亮该 ExpertCard
}

// handleConsensusUpdate
handleConsensusUpdate(data) {
  const targetList = data.record.type === 'consensus'
    ? this.consensusItems
    : this.disagreementItems;

  if (data.action === 'created') {
    targetList.push(data.record);
  } else if (data.action === 'updated') {
    const idx = targetList.findIndex(c => c.id === data.record.id);
    if (idx >= 0) targetList[idx] = data.record;
  } else if (data.action === 'resolved') {
    const idx = targetList.findIndex(c => c.id === data.record.id);
    if (idx >= 0) targetList[idx] = { ...targetList[idx], isResolved: true };
  }
}

// handleDiscussionEnded
handleDiscussionEnded(data) {
  this.status = 'ended';
  // 如有 streaming, 先完成它
  if (this.streaming) {
    this.streaming.isStreaming = false;
  }
  // Toast + 显示 "查看报告" 入口
}
```

---

## 6. 异常状态与边界处理

### 6.1 WebSocket 断连恢复

```
状态: connected → reconnecting → connected | disconnected

重连策略:
  attempt 1: 1s 后重连
  attempt 2: 2s 后重连  
  attempt 3: 4s 后重连 (指数退避, 最大 3 次)
  
  attempt > 3 → disconnected
    → Toast: "连接已断开，请刷新页面重新进入"
    → 显示手动刷新按钮 (覆盖在 Transcript 区域)
  
  reconnecting 期间:
    → wsStatus='reconnecting'
    → ExpertStatusPanel 顶部黄色提示条: "正在重新连接..."
    → 控制按钮禁用
    → 恢复连接后: replay missed events? → No (MVP简化: 重连后从REST拉取最新transcript
       snapshot, 可能丢失少量中间状态)
```

### 6.2 并发讨论隔离

```
Zustand Store 实例化策略:
  - useDiscussionStore → 全局单例 (HomePage 用)
  - usePanelStore → 全局单例 (同一时间只有一个编辑会话)
  - useStudioStore → 每个 StudioPage 独立实例
    (通过 discussionId key 区分, 切换讨论时调用 reset() + init())

隔离保证:
  - 每个 store 操作均带 discussionId 校验
  - 离开 StudioPage 时调用 reset() 清空所有状态
  - WebSocket 实例与 discussionId 绑定, 切换时 close 旧连接
```

### 6.3 页面生命周期

```
HomePage:
  mount → fetchList() → render
  unmount → 不清理 (列表缓存值得保留)

CreateDiscussionPage:
  mount → 初始化空表单
  unmount → 清理表单状态 (不提交)

PanelSetupPage:
  mount → initForDiscussion(id) → fetch generateList → render
  unmount → isDirty? confirm离开 : 清理

StudioPage:
  mount → fetchDetail(id) → initStore() → connect WS
  unmount → ws.close() → reset() → clearCurrent()

ReportPage:
  mount → fetchReport(id) → render
  unmount → 清理 (数据纯展示, 不需要 store)
```

---

## 7. 全局状态 (跨 Store)

### Session ID 管理

```typescript
// src/hooks/useSession.ts
function useSession() {
  // 1. 首次访问 → 生成 UUID v4 Session ID, 存入 localStorage
  // 2. 后续访问 → 从 localStorage 读取
  // 3. 提供 getSessionId(): string
}
```

- `creatorSessionId` 存储在 Discussion 的顶层字段
- API 请求头 `X-Session-Id` 自动注入
- WebSocket 连接 `?session_id=` 参数

### Toast 全局通知

```typescript
// 独立于页面 Store 的轻量全局状态
interface ToastStore {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}
```

---

## 8. URL 为唯一真相源 (Single Source of Truth)

```
所有页面跳转使用 React Router navigate(), 不通过 Store 驱动路由:

正确: navigate(`/studio/${discussionId}`)
错误: store.setCurrentPage('studio')

页面状态从 URL 参数派生:
  - HomePage: useSearchParams() → ?tab=live|ended
  - StudioPage: useParams() → discussionId
  - PanelSetupPage: useParams() → discussionId
  - ReportPage: useParams() → discussionId
```
