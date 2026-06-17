# AI Panel Studio — 前端组件规范文档

> **阶段**: DDD  
> **日期**: 2026-06-17  
> **设计来源**: HTML 原型 (home.html / ai-panel-studio.html) + SDD FRONTEND_GUIDELINES.md  
> **设计系统**: UI UX Pro Max v2.5 — Dark Mode OLED — Fira Code + Fira Sans

---

## 1. 组件树总览

```
<App>
  <AppLayout>
    ├── <TopBar />                         → 全局顶部导航
    │
    ├── [Route: /] <HomePage />
    │   ├── <HeroSection />
    │   │   └── <StatBadge />  ×3
    │   ├── <TabSwitcher />
    │   ├── <DiscussionList />             (live | ended)
    │   │   ├── <DiscussionCard />  ×N
    │   │   │   └── <PanelDots />
    │   │   └── <EmptyState />             (无数据时)
    │   └── <CreateDiscussionModal />
    │
    ├── [Route: /create] <CreateDiscussionPage />
    │   └── <TopicForm />
    │
    ├── [Route: /create/:id/panel] <PanelSetupPage />
    │   ├── <MemberCard />  ×(1+N)        (含主持人)
    │   ├── <MemberEditModal />
    │   ├── <ColorPicker />
    │   └── <GenerateProgress />
    │
    ├── [Route: /studio/:id] <StudioPage />
    │   └── <StudioLayout />
    │       ├── <ExpertStatusPanel />
    │       │   └── <ExpertCard />  ×N
    │       │       ├── <StatusBadge />
    │       │       └── <DesireMeter />
    │       ├── <TranscriptView />
    │       │   ├── <UtteranceItem />  ×N
    │       │   └── <StreamingText />
    │       ├── <ConsensusPanel />
    │       │   ├── <ConsensusItem />  ×N
    │       │   └── <EmptyState />
    │       └── <ControlBar />
    │
    └── [Route: /report/:id] <ReportPage />
        ├── <TranscriptView />            (复用，只读模式)
        └── <ConsensusPanel />            (复用，汇总模式)
```

---

## 2. 基础 UI 原子组件 (components/ui/)

### 2.1 `<Button />`

**来源原型**: ControlBar 按钮, Modal 操作按钮, Hero CTA

```typescript
interface ButtonProps {
  /** 语义变体 */
  variant: 'primary' | 'secondary' | 'danger' | 'ghost';
  /** 尺寸 */
  size?: 'sm' | 'md';
  /** 是否禁用 */
  disabled?: boolean;
  /** 加载中态 */
  loading?: boolean;
  /** 左侧图标 (SVG 组件) */
  iconLeft?: React.ReactNode;
  /** 点击回调 */
  onClick?: () => void;
  /** 按钮文本 */
  children: React.ReactNode;
  /** 额外类名 */
  className?: string;
}
```

**视觉映射** (来自原型 CSS):
- `primary`: `bg-[#22C55E] border-[#22C55E] text-black font-semibold`
- `secondary`: `bg-[#1E293B] border-[#334155] text-[#F8FAFC]`
- `danger`: `border-[#EF4444] text-[#EF4444]`, hover 反色
- `ghost`: 无背景无边框, `text-[#94A3B8]`
- `sm`: `py-[5px] px-[12px] text-xs`, `md`: `py-[8px] px-[18px] text-sm`
- `disabled`: `opacity-40 cursor-not-allowed`
- `loading`: 显示 `<Spinner />` 替代左侧图标

**交互规范**:
- `cursor-pointer`, `transition-all duration-200`
- `hover`: 亮度提升 / 边框颜色加深
- `active`: `scale-[0.97]` (除 ghost)
- `focus-visible`: `outline-2 outline-[#22C55E] outline-offset-2`

---

### 2.2 `<Input />`

**来源原型**: 创建讨论 Modal 话题输入, 最大轮次输入

```typescript
interface InputProps {
  /** 输入类型 */
  type?: 'text' | 'number';
  /** 占位字符串 */
  placeholder?: string;
  /** 最大字数 (text 类型) */
  maxLength?: number;
  /** 最小值/最大值 (number 类型) */
  min?: number;
  max?: number;
  /** 受控值 */
  value: string | number;
  /** 变更回调 */
  onChange: (value: string | number) => void;
  /** 是否错误态 */
  error?: boolean;
  /** 错误提示文案 */
  errorMessage?: string;
  /** 是否禁用 */
  disabled?: boolean;
}
```

**视觉映射**:
- 默认: `bg-[#1E293B] border border-[#334155] rounded-[6px] text-[#F8FAFC] px-[14px] py-[10px]`
- `focus`: `border-[#22C55E] shadow-[0_0_0_2px_rgba(34,197,94,0.15)]`
- `error`: `border-[#EF4444]`, 下方红色提示文字
- `disabled`: `opacity-40 cursor-not-allowed`
- 字数计数器 (text): 右下角 `{current}/{max}`, 超限变红

---

### 2.3 `<Modal />`

**来源原型**: CreateDiscussionModal

```typescript
interface ModalProps {
  /** 是否打开 */
  open: boolean;
  /** 关闭回调 */
  onClose: () => void;
  /** 模态框标题 */
  title: string;
  /** 是否点击遮罩关闭 */
  closeOnOverlay?: boolean;          // default true
  /** 内容 */
  children: React.ReactNode;
  /** 底部操作区 */
  footer?: React.ReactNode;
  /** 宽度变体 */
  size?: 'sm' | 'md' | 'lg';        // 420 / 480 / 640
}
```

**视觉映射**:
- Overlay: `fixed inset-0 bg-black/70 backdrop-blur-[4px] z-50`
- 面板: `bg-[#0F172A] border border-[#334155] rounded-[16px]`, 动画 `slideUp` (translateY 20→0, 250ms)
- 关闭: `Esc` 键 + 点击 overlay

---

### 2.4 `<Toast />`

**来源**: 全局通知（生成成功/失败、错误提示）

```typescript
interface Toast {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  duration?: number;                 // default 3000ms, 0=不自动关闭
}

interface ToastContainerProps {
  position?: 'top-right' | 'top-center' | 'bottom-center';
}
```

**状态机**: `entering (fadeIn+slideIn) -> visible (duration) -> exiting (fadeOut) -> removed`

---

### 2.5 `<Spinner />`

**来源**: Button loading, 嘉宾生成 loading, WebSocket 连接中

```typescript
interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';        // 16 / 24 / 32 px
  color?: string;                    // default var(--color-accent)
}
```

---

### 2.6 `<Badge />`

**来源**: 讨论卡片状态标识, 专家状态标识, 共识/分歧标签

```typescript
interface BadgeProps {
  variant: 'live' | 'ended' | 'consensus' | 'disagreement' | 'idle' | 'preparing' | 'speaking';
  dot?: boolean;                     // 是否带圆点
  children: React.ReactNode;
}
```

---

### 2.7 `<ColorPicker />`

**来源**: 嘉宾编辑弹窗 — 颜色编辑

```typescript
interface ColorPickerProps {
  value: string;                     // HEX
  onChange: (color: string) => void;
  presets?: string[];                // 默认提供 10 个预选色
}
```

---

## 3. 通用业务组件 (components/)

### 3.1 `<DiscussionCard />`

**来源原型**: home.html — `.card`

```
┌─────────────────────────────────────────────────────┐
│ ▌ [主题文本                          ]  [直播中 ●] → │
│ ▌ 👥 4位专家 · 💬 8条发言 · 🔄 第3轮 · 时间         │
│ ▌ [●] [●] [●] [●]                                    │
└─────────────────────────────────────────────────────┘
```

```typescript
interface DiscussionCardProps {
  discussion: DiscussionSummary;
  onNavigate: (id: string, status: 'live' | 'ended') => void;
}
```

- `status === 'live'`: 左侧绿色指示条 + 呼吸动画, Badge "直播中"
- `status === 'ended'`: 左侧灰色指示条, Badge "已结束"
- `hover`: `translateX(3px)`, 边框颜色加深, 箭头 `→` 右移
- `focus`: 键盘可操作, Enter 触发导航
- PanelDots: 展示专家颜色圆点 (最多 5 个, 超出省略为 `+N`)

---

### 3.2 `<MemberCard />`

**来源原型**: ai-panel-studio.html — `.expert-card`

```
┌──────────────────────┐
│ ▌ [头像] 姓名        │
│           Title      │
│ 立场文字 (斜体)       │
│ [待机 ●]              │
│ 💭 关注点摘要         │
│ 发言欲望 ████░░ 85    │
└──────────────────────┘
```

```typescript
interface MemberCardProps {
  member: PanelMember;
  status?: ExpertStatus;             // 演播厅模式独有
  editable?: boolean;                // 编辑模式 (嘉宾编辑页)
  onEdit?: (member: PanelMember) => void;
  onRegenerate?: (memberId: string) => void;
}
```

**三种模式**:

| 模式 | 触发条件 | 点击行为 |
|------|----------|----------|
| 展示模式 | `!editable && !status` (嘉宾编辑页只读) | 无操作 |
| 编辑模式 | `editable === true` | 打开 `<MemberEditModal />` |
| 演播厅模式 | `status` 存在 | 显示状态详情 (Toast/Dialog) |

---

### 3.3 `<StatusBadge />`

**来源原型**: `.status-badge`

```typescript
interface StatusBadgeProps {
  status: 'idle' | 'preparing' | 'speaking';
}
```

- `idle`: 灰底灰字, `--status-idle: #64748B`
- `preparing`: 橙底橙字, 呼吸动画 (`pulse-badge 0.8s`)
- `speaking`: 蓝底蓝字, 快速呼吸 (`pulse-badge 0.5s`)
- 三种均带圆点 + 中文文本: `待机 | 准备发言 | 发言中`

---

### 3.4 `<DesireMeter />`

**来源原型**: `.desire-meter`

```typescript
interface DesireMeterProps {
  value: number;                     // 0.00 - 1.00
  color?: string;                    // 嘉宾颜色
}
```

- 进度条 `transition: width 400ms ease`
- 右侧数值: Fira Code 等宽字体, 0-100 整数

---

### 3.5 `<ExpertStatusPanel />`

**来源原型**: ai-panel-studio.html — 左侧面板 / 横向 strip

```typescript
interface ExpertStatusPanelProps {
  members: PanelMember[];
  statuses: Map<string, ExpertStatus>;
}
```

- 循环渲染 `<ExpertCard member status />` ×N
- 主持人排第一位 (`sort_order=0`), 其余按 `sort_order` 排列

---

### 3.6 `<UtteranceItem />`

**来源原型**: `.utterance`

```typescript
interface UtteranceItemProps {
  utterance: Utterance;
  member: PanelMember;
  isLast?: boolean;
}
```

- 左侧 3px 竖线 (发言人颜色)
- 头部: 发言人姓名 (颜色) + Title + 发言类型 Badge
- 正文: 常规文本 `leading-relaxed`
- 时间戳: Fira Code 等宽字体
- 入场: `fadeInUp` 动画 (opacity 0→1, translateY 12→0, 350ms)
- `type === 'summary'`: 特殊样式 — 绿色边框高亮, 全宽

---

### 3.7 `<TranscriptView />`

**来源原型**: ai-panel-studio.html — 中间面板

```typescript
interface TranscriptViewProps {
  utterances: Utterance[];
  members: PanelMember[];            // 用于查找发言人信息
  streaming?: StreamingUtterance | null;
  readonly?: boolean;                // 报告模式无流式
}
```

- 渲染 `<UtteranceItem />` 列表
- 若 `streaming` 存在 → 尾部追加 `<StreamingText />`
- **自动滚动**: `scrollTop = scrollHeight` (仅在用户未手动上滚时); 检测: 若 `scrollTop + clientHeight >= scrollHeight - 100` 则自动跟底
- `readonly`: 不显示 streaming, 纯静态列表

---

### 3.8 `<StreamingText />`

**来源原型**: `.streaming-cursor`

```typescript
interface StreamingTextProps {
  content: string;                   // 当前已累积的文本
  isStreaming: boolean;
}
```

- 文本末尾显示闪烁光标 `▍` (CSS `@keyframes blink`)
- `isStreaming === false` → 光标消失
- 字体颜色与发言人一致

---

### 3.9 `<ConsensusItem />`

**来源原型**: `.consensus-item`

```typescript
interface ConsensusItemProps {
  item: ConsensusRecord;
}
```

- 类型 Badge: `✓ 共识` (绿底) / `⚡ 分歧` (橙底)
- 已化解标识: `is_resolved` → 绿色小标签
- 置信度指示: 圆点颜色 (high≥0.8 绿 / mid≥0.5 橙 / low<0.5 红)
- 元数据行: 置信度百分比 + 所属轮次
- 入场: `fadeInUp` 动画

---

### 3.10 `<ConsensusPanel />`

**来源原型**: ai-panel-studio.html — 右侧面板

```typescript
interface ConsensusPanelProps {
  items: ConsensusRecord[];
  mode?: 'live' | 'report';         // live: 实时更新, report: 汇总 (默认 consensus 和 disagreement 合并)
}
```

- 空状态: icon + "讨论刚开始，暂无共识或分歧记录"
- `mode='report'`: 合并共识和分歧到一个列表, 不再显示 "实时" 字样

---

### 3.11 `<ControlBar />`

**来源原型**: ai-panel-studio.html — 底栏

```typescript
interface ControlBarProps {
  status: 'live' | 'paused' | 'ended';
  currentRound: number;
  totalUtterances: number;
  maxRounds: number | null;
  isCreator: boolean;                // 非创建者隐藏控制按钮
  onPause: () => void;
  onResume: () => void;
  onAdvance: () => void;
  onEnd: () => void;
}
```

**按钮显隐逻辑**:

| Discussion Status | 暂停 | 继续 | 下一轮 | 结束 |
|-------------------|------|------|--------|------|
| `live` | ✓ 显示 | ✗ | ✓ 显示 | ✓ 显示 |
| `paused` | ✗ | ✓ 显示 | ✓ 显示 | ✓ 显示 |
| `ended` | ✗ | ✗ | ✗ | ✗ |

- 右侧状态文字: `轮次 {currentRound}/{maxRounds||'∞'} · 发言 {totalUtterances} 条`
- `isCreator === false`: 全部按钮隐藏, 仅显示状态文字

---

### 3.12 `<PanelDots />`

**来源原型**: home.html — `.card__panel-preview`

```typescript
interface PanelDotsProps {
  members: PanelMember[];            // 仅 experts
  maxDisplay?: number;               // 默认 5
}
```

- 渲染最多 `maxDisplay` 个彩色圆点 (专家专属颜色)
- 超出部分显示 `+N` 灰色圆点

---

### 3.13 `<EmptyState />`

**来源原型**: home.html / ai-panel-studio.html — `.empty-state`

```typescript
interface EmptyStateProps {
  icon?: string;                     // emoji 作为占位 (后续替换 SVG)
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}
```

---

## 4. 页面级组件 (features/)

### 4.1 `HomePage` — 首页

**来源原型**: home.html

| 状态 | 条件 | UI |
|------|------|----|
| 正常 | 列表有数据 | Hero + TabSwitcher + CardGrid |
| 空 (进行中) | liveDiscussions=[] | Hero + TabSwitcher + EmptyState ("暂无进行中的讨论") |
| 空 (已结束) | endedDiscussions=[] | EmptyState ("暂无已结束讨论") |
| 加载 | API 请求中 | Card Skeleton ×3 |

**Tab 切换**: `live | ended`, URL 参数驱动 `?tab=live|ended`

**数据来源**: `useDiscussionStore` → `GET /api/discussions`

---

### 4.2 `CreateDiscussionPage` — 创建讨论

**来源原型**: home.html Modal → 独立页面化

| 状态 | 条件 | UI |
|------|------|----|
| 填写中 | 话题为空 | "生成嘉宾阵容" 按钮禁用 |
| 可提交 | 话题 1-200 字 | 按钮可用 |
| 错误 | 话题 > 200 字 | 输入框红色, 字数计数器红色 |
| 提交中 | POST 请求中 | 按钮 loading, 页面无其他操作 |
| 失败 | API 错误 | Toast 错误信息, 按钮恢复 |

**流程**: 填写表单 → `POST /api/discussions` → 获得 `discussionId` → 跳转 `/create/:id/panel`

---

### 4.3 `PanelSetupPage` — 嘉宾阵容编辑

**来源原型**: 无独立原型 (Modal 流程扩展)

**状态机**:

```
┌────────┐  POST /panel/generate   ┌──────────┐  编辑完毕 PUT /panel  ┌──────────┐
│ 加载中  │ ──────────────────────→ │  编辑态   │ ───────────────────→ │  确认跳转  │
│(spinner)│                         │ editable │                       │ → /studio  │
└────────┘                         └──────────┘                       └──────────┘
                                          │
                                    ┌─────┴──────┐
                                    ▼            ▼
                              ┌──────────┐ ┌──────────┐
                              │ 单体重生   │ │ 全体重生   │
                              │(单个spinner)│ │(全部spinner)│
                              └──────────┘ └──────────┘
```

**关键交互**:
- 点击嘉宾卡片 → `<MemberEditModal />` (姓名/Title/立场/颜色)
- 颜色编辑 → `<ColorPicker />`
- 单体重生 → `POST /panel/generate { regenerate_member_id }` → 替换该位
- 全体重生 → 二次确认弹窗 → 全部替换
- 确认 → `PUT /panel` → 跳转 `/studio/:id`

---

### 4.4 `StudioPage` — 演播厅

**来源原型**: ai-panel-studio.html

**初始化流程**:
```
1. 进入页面 → GET /api/discussions/:id (获取讨论详情 + Transcript 历史)
2. 建立 WebSocket 连接 → ws://host/ws/discussions/:id
3. 接收 initial_snapshot (或通过 REST 获取)
4. 进入实时更新循环
```

**WebSocket 事件分发**:

| 事件 | Store 方法 | UI 效果 |
|------|-----------|---------|
| `expert_status` | `updateExpertStatus()` | 专家卡片状态灯切换 + 关注点摘要更新 + 欲望值条动画 |
| `utterance_token` | `appendToken()` | Transcript 追加文本 + 光标闪烁 |
| `utterance_complete` | `completeUtterance()` | 发言完毕, 光标消失, 新行追加 |
| `consensus_update` | `upsertConsensus()` | 共识/分歧列表动态插入 / 更新 |
| `discussion_paused` | `setStatus('paused')` | 控制栏按钮切换 |
| `discussion_resumed` | `setStatus('live')` | 控制栏按钮切换 |
| `discussion_ended` | `setStatus('ended')` | 控制栏全禁用, 显示总结入口 |

**子组件**: `<StudioLayout />` (响应式容器)

---

### 4.4.1 `<StudioLayout />` — 响应式布局容器

**来源原型**: `.studio` grid

```typescript
interface StudioLayoutProps {
  expertPanel: React.ReactNode;      // <ExpertStatusPanel />
  transcript: React.ReactNode;       // <TranscriptView />
  consensusPanel: React.ReactNode;   // <ConsensusPanel />
}
```

**断点切换**:

| 宽度 | CSS | 专家面板 | Transcript | 共识面板 |
|------|-----|----------|------------|----------|
| ≥1400px | `grid-cols-[280px_1fr_320px]` | 左侧竖列 | 中间 | 右侧竖列 |
| 800-1399px | `grid-cols-[1fr_300px]` + expertStrip | 隐藏; 横向滚动条 | 左侧 | 右侧 |
| <800px | `grid-cols-1` | 三区垂直堆叠, `max-height:35vh` |  |  |

- `≥1400px`: 使用 `<aside>` 侧栏
- `800-1399px`: `<ExpertStatusPanel />` 变为 `<ExpertStrip />` (横向, 卡片压缩)
- `<800px`: 三区块垂直堆叠, 各自独立滚动

---

### 4.5 `ReportPage` — 讨论报告

**来源原型**: 无独立原型 (演播厅结束后的只读视图)

**组件复用**:
- `<TranscriptView readonly />` — 完整转录
- `<ConsensusPanel mode="report" />` — 共识/分歧汇总
- 主持人总结 (最后一条 utterance, 特殊高亮)

**数据来源**: `GET /api/discussions/:id/report`

---

## 5. 页面路由入口 (pages/)

页面层为薄层 (< 30 行), 仅组合 features 和 store。

| 文件 | 组合内容 |
|------|----------|
| `HomePage.tsx` | `<HeroSection />` + `<TabSwitcher />` + `<DiscussionList />` |
| `CreateDiscussionPage.tsx` | `<TopicForm />` + 跳转逻辑 |
| `PanelSetupPage.tsx` | `<MemberCard />` ×N + `<MemberEditModal />` + `<ColorPicker />` |
| `StudioPage.tsx` | `<StudioLayout />` 包裹三个 Panel + `<ControlBar />` |
| `ReportPage.tsx` | `<TranscriptView readonly />` + `<ConsensusPanel mode="report" />` |

---

## 6. 路由守卫规则

| 路由 | 条件 | 行为 |
|------|------|------|
| `/studio/:id` | `discussion === null` (不存在) | redirect `/` + Toast "讨论不存在" |
| `/studio/:id` | `discussion.status === 'ended'` | redirect `/report/:id` |
| `/create/:id/panel` | `discussion === null` | redirect `/` |
| `/create/:id/panel` | `discussion.status !== 'pending'` | 若 panel 已确认 → redirect `/studio/:id` |
| `/report/:id` | `discussion.status === 'live'` | 正常显示当前进度 (不重定向) |

---

## 7. 全局组件

| 组件 | 渲染位置 | 说明 |
|------|----------|------|
| `<TopBar />` | `<AppLayout />` | Brand + 话题标签 + 直播状态 (仅演播厅页显示话题) |
| `<ToastContainer />` | `<AppLayout />` | 固定定位, 全局通知 |
| `<Spinner />` | 按需 | 可独立使用 |

---

## 8. 组件职责矩阵

| 组件 | Props 驱动 | 有内部状态 | 调用 Store | 发起 API | WebSocket |
|------|-----------|-----------|-----------|----------|----------|
| Button | ✓ | ✗ | ✗ | ✗ | ✗ |
| Input | ✓ (受控) | ✗ | ✗ | ✗ | ✗ |
| Modal | ✓ (open) | ✗ | ✗ | ✗ | ✗ |
| Toast | — | ✓ | ✓ (全局) | ✗ | ✗ |
| Spinner | ✓ | ✗ | ✗ | ✗ | ✗ |
| Badge | ✓ | ✗ | ✗ | ✗ | ✗ |
| ColorPicker | ✓ (受控) | ✓ (拾色器) | ✗ | ✗ | ✗ |
| DiscussionCard | ✓ | ✗ | ✗ | ✗ | ✗ |
| MemberCard | ✓ | ✗ | ✗ | ✗ | ✗ |
| StatusBadge | ✓ | ✗ | ✗ | ✗ | ✗ |
| DesireMeter | ✓ | ✗ | ✗ | ✗ | ✗ |
| ExpertStatusPanel | ✓ | ✗ | ✗ | ✗ | ✗ |
| UtteranceItem | ✓ | ✗ | ✗ | ✗ | ✗ |
| TranscriptView | ✓ | ✓(autoScroll) | ✗ | ✗ | ✗ |
| StreamingText | ✓ | ✗ | ✗ | ✗ | ✗ |
| ConsensusItem | ✓ | ✗ | ✗ | ✗ | ✗ |
| ConsensusPanel | ✓ | ✗ | ✗ | ✗ | ✗ |
| ControlBar | ✓ | ✗ | ✗ | ✗ | ✗ |
| PanelDots | ✓ | ✗ | ✗ | ✗ | ✗ |
| EmptyState | ✓ | ✗ | ✗ | ✗ | ✗ |
| **HomePage** | ✗ | ✗ | ✓ (discussion) | ✓ (list) | ✗ |
| **CreateDiscussionPage** | ✗ | ✓ (form) | ✗ | ✓ (create) | ✗ |
| **PanelSetupPage** | ✗ | ✓ (edit) | ✓ (panel) | ✓ (generate/confirm) | ✗ |
| **StudioPage** | ✗ | ✗ | ✓ (studio) | ✗ | ✓ (全部事件) |
| **ReportPage** | ✗ | ✗ | ✗ | ✓ (report) | ✗ |
