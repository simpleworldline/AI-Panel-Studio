# AI Panel Studio — 前端组件文档

> **阶段**: DDD  
> **日期**: 2026-06-18  

---

## 1. 组件架构总览

```
src/
├── components/
│   ├── ui/                    ← 原子/分子 UI 组件（无业务语义）
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Spinner.tsx
│   │   ├── Badge.tsx
│   │   ├── Modal.tsx
│   │   ├── Toast.tsx         ← ToastContainer（容器）
│   │   └── ColorPicker.tsx
│   │
│   ├── DiscussionCard.tsx     ← 讨论列表卡片
│   ├── MemberCard.tsx         ← 嘉宾卡片
│   ├── EmptyState.tsx         ← 空状态占位
│   ├── ErrorBoundary.tsx      ← 全局错误边界
│   ├── TranscriptView.tsx     ← 讨论记录视图（容器）
│   ├── UtteranceItem.tsx      ← 单条发言
│   ├── StreamingText.tsx      ← 流式打字机文本
│   ├── ExpertStatusPanel.tsx  ← 嘉宾状态面板（容器）
│   ├── ConsensusPanel.tsx     ← 共识/分歧面板（容器）
│   ├── ConsensusItem.tsx      ← 单条共识/分歧
│   ├── ControlBar.tsx         ← 讨论控制栏
│   └── PanelDots.tsx          ← 嘉宾颜色点阵
│
├── layouts/
│   └── AppLayout.tsx          ← 全局布局（Header + Outlet）
│
├── pages/                     ← 路由页面（薄层，组合组件）
│   ├── HomePage.tsx
│   ├── CreateDiscussionPage.tsx
│   ├── PanelSetupPage.tsx
│   ├── StudioPage.tsx
│   └── ReportPage.tsx
│
├── store/                     ← Zustand 状态管理
├── api/                       ← HTTP API 封装
├── ws/                        ← WebSocket 客户端
├── types/                     ← TypeScript 类型
├── utils/                     ← 工具函数
│
├── App.tsx                    ← 路由定义 + ErrorBoundary + Toast
├── main.tsx                   ← ReactDOM 入口
└── index.css                  ← Tailwind + 演播厅主题变量
```

**组件分层原则：**

| 层级 | 位置 | 职责 |
|------|------|------|
| `pages/` | 路由入口 | 仅组合 features 和 components，不含复杂业务逻辑 |
| `components/ui/` | 基础组件 | 无业务语义的原子/分子组件，纯 props 驱动 |
| `components/` | 领域组件 | 可跨页面复用的演播厅组件，通过 props 驱动 |
| `layouts/` | 布局 | 全局框架结构 |

---

## 2. 基础 UI 组件 (`components/ui/`)

### 2.1 `Button`

多态按钮组件。

**Props：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `variant` | `'primary' \| 'secondary' \| 'ghost' \| 'danger'` | `'primary'` | 按钮变体 |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | 尺寸 |
| `loading` | `boolean` | `false` | 加载态（显示 spinner + 禁用） |
| `disabled` | `boolean` | — | 禁用态 |
| `children` | `ReactNode` | *必填* | 按钮内容 |
| `className` | `string` | `''` | 额外样式 |
| `...props` | `ButtonHTMLAttributes` | — | 透传原生属性 |

**变体样式：**

| 变体 | 背景 | 文字 | 边框 |
|------|------|------|------|
| `primary` | `var(--color-studio-info)` | 白色 | 无 |
| `secondary` | `var(--color-studio-elevated)` | 主色 | `studio-border` |
| `ghost` | 透明 | 次色 | 无 |
| `danger` | `var(--color-studio-destructive)` | 白色 | 无 |

**使用示例：**

```tsx
<Button variant="primary" size="lg" loading={isSubmitting} onClick={handleSubmit}>
  生成嘉宾阵容
</Button>

<Button variant="secondary" size="sm" onClick={handlePause}>
  暂停
</Button>
```

---

### 2.2 `Input`

带标签和验证状态的输入框。

**Props：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `label` | `string` | — | 标签文本 |
| `error` | `string` | — | 错误信息（出现时变红） |
| `helperText` | `string` | — | 辅助提示（error 存在时隐藏） |
| `className` | `string` | `''` | 额外样式 |
| `id` | `string` | 自动生成 | input id（关联 label） |
| `...props` | `InputHTMLAttributes` | — | 透传原生属性 |

**使用示例：**

```tsx
<Input
  label="讨论话题"
  placeholder="例如：AI 是否应该具备自我意识？"
  value={topic}
  onChange={(e) => setTopic(e.target.value)}
  maxLength={200}
  error={topic.length > 200 ? '最多 200 字' : undefined}
  helperText={`${topic.length}/200`}
/>
```

---

### 2.3 `Spinner`

加载旋转指示器。

**Props：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | `w-4`, `w-8`, `w-12` |
| `className` | `string` | `''` | 额外样式 |

**使用示例：**

```tsx
<Spinner size="lg" />
```

---

### 2.4 `Badge`

徽标/标签组件。

**Props：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `children` | `ReactNode` | *必填* | 内容 |
| `color` | `string` | — | hex 颜色（用于 dot/outline/solid） |
| `variant` | `'solid' \| 'outline' \| 'dot'` | `'solid'` | 变体 |
| `className` | `string` | `''` | 额外样式 |

**变体说明：**

| 变体 | 效果 |
|------|------|
| `solid` | 纯色背景 + 白色文字 |
| `outline` | 透明背景 + 彩色边框 + 彩色文字 |
| `dot` | 彩色圆点 + 灰色文字 |

**使用示例：**

```tsx
<Badge color="#6366F1" variant="dot">待机</Badge>
<Badge color="#34D399">共识</Badge>
```

---

### 2.5 `Modal`

对话框/弹出面板。

**Props：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `open` | `boolean` | *必填* | 是否打开 |
| `onClose` | `() => void` | *必填* | 关闭回调（Escape/点击遮罩触发） |
| `title` | `string` | *必填* | 标题 |
| `children` | `ReactNode` | *必填* | 内容 |
| `footer` | `ReactNode` | — | 底部操作区 |

**使用示例：**

```tsx
<Modal
  open={editingHost}
  onClose={() => setEditingHost(false)}
  title="编辑主持人"
  footer={
    <Button variant="primary" size="sm" onClick={() => setEditingHost(false)}>
      完成
    </Button>
  }
>
  <div className="flex flex-col gap-3">
    <Input label="姓名" value={name} onChange={...} />
    <ColorPicker value={color} onChange={...} />
  </div>
</Modal>
```

---

### 2.6 `Toast` / `ToastContainer`

全局 Toast 通知容器。**非直接使用组件，通过 `useToastStore` 调用。**

**Store 接口：**

```typescript
// 添加 Toast
useToastStore.getState().addToast({
  type: 'info' | 'success' | 'warning' | 'error',
  message: '操作成功',
});

// Toast 4s 后自动消失，也可点击关闭
```

**使用示例：**

```tsx
const addToast = useToastStore((s) => s.addToast);
addToast({ type: 'success', message: '讨论创建成功' });
addToast({ type: 'error', message: '操作失败，请重试' });
```

**容器渲染（App.tsx 中全局挂载）：**

```tsx
<ToastContainer />
```

---

### 2.7 `ColorPicker`

嘉宾颜色选择器。

**Props：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `value` | `string` | *必填* | 当前选中颜色 (hex) |
| `onChange` | `(color: string) => void` | *必填* | 颜色变更回调 |

**预设颜色：** 靛蓝 `#6366F1`、赤红 `#EF4444`、翠绿 `#10B981`、琥珀 `#F59E0B`、紫罗 `#8B5CF6`、玫粉 `#EC4899`、青蓝 `#06B6D4`、橘橙 `#F97316`

**使用示例：**

```tsx
<ColorPicker value={member.color} onChange={(c) => updateMember({ color: c })} />
```

---

## 3. 领域组件 (`components/`)

### 3.1 `DiscussionCard`

首页讨论列表卡片。

**Props：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `discussion` | `DiscussionSummary` | 讨论摘要数据 |

**行为：**
- 进行中 → 点击跳转 `/studio/:id`
- 已结束 → 点击跳转 `/report/:id`
- 悬停：边框高亮 + 标题变色

**内部展示：**
- 话题标题（最多 2 行截断）
- 状态徽标（进行中=绿灯、已暂停=黄灯、已结束=灰灯）
- 嘉宾名称预览（最多 4 人）
- 底部元信息：嘉宾数、当前轮次、相对时间

---

### 3.2 `MemberCard`

嘉宾信息卡片。

**Props：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `member` | `PanelMember` | *必填* | 嘉宾数据 |
| `onEdit` | `() => void` | — | 编辑回调 |
| `onRegenerate` | `() => void` | — | 重生回调 |
| `showActions` | `boolean` | `false` | 是否显示操作按钮 |

**展示内容：**
- 左侧：彩色头像圆（首字）+ 姓名 + 角色徽标
- 右侧：Title、立场描述
- 底部（`showActions=true`）：编辑 / 重新生成 链接
- 左侧彩色边框（`borderLeftWidth: 3px`）

---

### 3.3 `EmptyState`

空状态占位组件。

**Props：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `icon` | `ReactNode` | SVG 图标（可选） |
| `title` | `string` | 主标题 |
| `description` | `string` | 描述文本（可选） |
| `action` | `ReactNode` | 操作按钮（可选） |

**使用示例：**

```tsx
<EmptyState
  title="暂无进行中的讨论"
  description="发起一个新讨论，成为第一位主持人"
  icon={<svg>...</svg>}
/>
```

---

### 3.4 `ErrorBoundary`

全局 React 错误边界。**在 App.tsx 中包裹所有路由。**

**行为：**
- 捕获子组件渲染错误
- 显示错误信息 + "返回首页"按钮
- 点击按钮清除错误状态并跳转首页

---

### 3.5 `TranscriptView`

讨论记录视图 — **容器组件**，负责列表渲染 + 自动滚动。

**Props：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `utterances` | `UtteranceDisplay[]` | 已完成发言列表 |
| `streaming` | `StreamingUtterance \| null` | 当前流式发言 |

**行为：**
- 无发言且无流式 → 显示 `EmptyState`（"等待讨论开始"）
- 有发言 → 渲染 `UtteranceItem` 列表 + 当前流式发言块
- 新发言/新 token → `scrollIntoView({ behavior: 'smooth' })`

**子组件使用：**
- `UtteranceItem` — 已完成发言
- `StreamingText` — 流式发言 + 光标动画
- `EmptyState` — 空状态

---

### 3.6 `UtteranceItem`

单条已完成发言。

**Props：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `utterance` | `UtteranceDisplay` | 发言数据 |

**展示内容：**
- 左侧：彩色头像圆（成员首字）
- 右上：姓名（彩色）+ Title + 类型徽标（开场/发言/提问/回应/总结）+ 时间
- 下：发言正文（`whitespace-pre-wrap`）

**动画：** 入场 `animate-fade-in`（opacity + translateY）

---

### 3.7 `StreamingText`

流式打字机文本 + 闪烁光标。

**Props：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `text` | `string` | 已累积文本 |
| `isStreaming` | `boolean` | 是否还在接收 token |
| `memberColor` | `string` | 光标颜色 |

**行为：**
- `isStreaming=true` → 显示闪烁光标 `|`
- `isStreaming=false` → 隐藏光标

---

### 3.8 `ExpertStatusPanel`

嘉宾状态面板 — **容器组件**。

**Props：**

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `members` | `PanelMember[]` | *必填* | 嘉宾列表 |
| `statuses` | `Record<string, ExpertStatus>` | *必填* | 状态映射 |
| `compact` | `boolean` | `false` | 紧凑模式（横向排列） |

**行为：**
- `compact=true` → 横向滚动容器，每张卡片 `w-[200px]`
- `compact=false` → 纵向堆叠
- 发言中的嘉宾卡片 → `animate-pulse-glow` + 边框高亮
- 无嘉宾 → "暂无嘉宾" 提示

**每张卡片展示：**
- 颜色圆点 + 姓名 + 角色标识（主持/嘉宾）
- 状态标签（待机=灰色、准备中=黄色、发言中=蓝色）
- 当前关注点摘要（`line-clamp-2`）

---

### 3.9 `ConsensusPanel`

共识/分歧面板 — **容器组件**。

**Props：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `items` | `ConsensusItemDisplay[]` | 共识+分歧混合列表 |

**行为：**
- 空列表 → `EmptyState`（"暂无共识或分歧"）
- 有数据 → 渲染 `ConsensusItem` 列表

---

### 3.10 `ConsensusItem`

单条共识或分歧记录。

**Props：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `item` | `ConsensusItemDisplay` | 记录数据 |

**视觉区分：**

| 类型 | 背景 | 边框 | 徽标 |
|------|------|------|------|
| `consensus` | 绿色 10% | 绿色 30% | 绿色"共识" |
| `disagreement` | 橙色 10% | 橙色 30% | 橙色"分歧" |

**展示内容：**
- 类型徽标 + 置信度 + 已化解标识
- 标题
- 描述文本

---

### 3.11 `ControlBar`

讨论控制栏 — 底部固定操作区。

**Props：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `status` | `'live' \| 'paused' \| 'ended'` | 当前状态 |
| `currentRound` | `number` | 当前轮次 |
| `totalUtterances` | `number` | 发言总数 |
| `maxRounds` | `number \| null` | 最大轮次 |
| `isCreator` | `boolean` | 是否创建者 |
| `onPause` | `() => void` | 暂停回调 |
| `onResume` | `() => void` | 继续回调 |
| `onAdvance` | `() => void` | 推进回调 |
| `onEnd` | `() => void` | 结束回调 |

**按钮逻辑：**

| 状态 / 角色 | 暂停 | 继续 | 下一轮 | 结束 |
|-------------|------|------|--------|------|
| `live` + 创建者 | ✅ | — | ✅ | ✅ |
| `paused` + 创建者 | — | ✅ | — | ✅ |
| `ended` + 创建者 | — | — | — | — |
| 非创建者 | — | — | — | — |

---

### 3.12 `PanelDots`

嘉宾颜色点阵预览（用于讨论卡片）。

**Props：**

| 属性 | 类型 | 说明 |
|------|------|------|
| `count` | `number` | 点数（= 嘉宾数） |
| `className` | `string` | 额外样式 |

---

## 4. 布局组件

### 4.1 `AppLayout`

全局布局框架。

**结构：**

```
┌─────────────────────────────────────┐
│  Header (固定顶栏)                    │
│  AI Panel Studio  Logo  +  "AI演播厅" │
├─────────────────────────────────────┤
│                                     │
│  <Outlet />  (页面内容区 flex-1)      │
│                                     │
└─────────────────────────────────────┘
```

**路由包裹：**

```tsx
<Route element={<AppLayout />}>
  <Route index element={<HomePage />} />
  <Route path="create" element={<CreateDiscussionPage />} />
  {/* ... */}
</Route>
```

---

## 5. 页面组件

### 5.1 `HomePage` — 首页

**路由：** `/`

**功能：**
- 讨论列表（进行中/已结束 Tab 切换）
- "发起新讨论" 按钮
- 加载态：`Spinner`
- 错误态：错误信息 + 重试按钮
- 空态：`EmptyState`

**数据源：** `useDiscussionStore`

---

### 5.2 `CreateDiscussionPage` — 创建讨论

**路由：** `/create`

**功能：**
- 话题输入（1-200字 + 实时计数）
- 嘉宾人数滑块（2-8）
- 最大轮次选择（可选，不限/3/5/8/10/15/20）
- "生成嘉宾阵容" 按钮（话题为空时禁用）
- 创建成功后跳转 `/create/:id/panel`

**数据源：** 本地 `useState` + `createDiscussion()` API

---

### 5.3 `PanelSetupPage` — 嘉宾阵容编辑

**路由：** `/create/:discussionId/panel`

**功能：**
- 进入时自动调用 `generatePanel()`
- 主持人卡片 + 嘉宾卡片网格（2列）
- 编辑弹窗（姓名/Title/立场/颜色拾取器）
- 单体重生 / 全体重生
- "确认阵容，进入演播厅" → 跳转 `/studio/:id`

**数据源：** `usePanelStore`

---

### 5.4 `StudioPage` — 演播厅

**路由：** `/studio/:discussionId`

**功能：**
- WebSocket 实时连接 + 3s 轮询兜底
- 已结束讨论自动重定向 `/report/:id`
- 三栏布局：嘉宾状态 | 讨论记录 | 共识分歧
- 响应式断点切换
- 底部控制栏
- 结束状态：显示"查看讨论报告"按钮

**数据源：** `useDiscussionStore`（初始化）+ `useStudioStore`（实时）

---

### 5.5 `ReportPage` — 讨论报告

**路由：** `/report/:discussionId`

**功能：**
- 讨论完整 Transcript（按时间序）
- 共识/分歧汇总
- 元信息：嘉宾数、发言数、轮次
- "返回首页" 按钮

**数据源：** `useDiscussionStore.fetchDetail()`

---

## 6. 响应式布局策略

### 6.1 StudioPage 三栏切换

| 断点 | 布局 | Grid |
|------|------|------|
| ≥1400px | 三栏 | `280px 1fr 320px` |
| 800-1399px | 两栏 | 专家状态移至顶部横排，左侧栏隐藏 (`.hidden.lg:flex`) |
| <800px | 单栏 | 垂直堆叠 (默认 block 布局覆盖 grid) |

### 6.2 首页卡片网格

| 断点 | 列数 |
|------|------|
| ≥1024px | 3 列 |
| ≥640px | 2 列 |
| <640px | 1 列 |

### 6.3 嘉宾编辑网格

| 断点 | 列数 |
|------|------|
| ≥640px | 2 列 |
| <640px | 1 列 |

---

## 7. 动画规范

| 场景 | 动画 | 时长 | 缓动 |
|------|------|------|------|
| 列表项入场 | `fadeIn` (opacity 0→1 + translateY 4→0) | 200ms | ease-out |
| 发言中边框光晕 | `pulseGlow` (box-shadow 循环) | 2s | ease-in-out |
| 流式文本光标 | `blinkCursor` (opacity 闪烁) | 800ms | ease-in-out |
| 发言中状态指示灯 | `statusPulse` (scale 循环) | 1.5s | ease-in-out |
| 悬停反馈 | `transition-colors` | 150ms | — |
| 卡片入场 | `animate-fade-in` | 200ms | ease-out |

**无障碍：** 所有动画在 `prefers-reduced-motion: reduce` 时禁用。

---

## 8. Z-Index 分层

| 层级 | CSS 变量 | 值 | 用途 |
|------|----------|----|------|
| 基础 | `--z-base` | 0 | 内容区 |
| 粘性 | `--z-sticky` | 20 | 区域标题栏 sticky |
| 覆盖 | `--z-overlay` | 30 | 下拉菜单 |
| 模态 | `--z-modal` | 50 | Modal / Toast |

---

## 9. 主题变量一览

```css
/* 背景层级 */
--color-studio-bg: #0F1117         /* 主背景 */
--color-studio-elevated: #1A1D2E   /* 抬高背景 */
--color-studio-card: #1E2133       /* 卡片背景 */
--color-studio-border: #2A2D3E     /* 边框 */
--color-studio-border-subtle: #1E2032

/* 文字层级 */
--color-studio-fg: #F1F5F9         /* 正文 */
--color-studio-fg-muted: #64748B   /* 辅助文字 */
--color-studio-fg-subtle: #475569  /* 弱化文字 */

/* 语义色 */
--color-studio-gold: #F0C060       /* 主持人 */
--color-studio-consensus: #34D399  /* 共识 */
--color-studio-disagreement: #FB923C /* 分歧 */
--color-studio-success: #22C55E    /* 成功 */
--color-studio-warning: #F59E0B    /* 警告 */
--color-studio-destructive: #EF4444 /* 危险/错误 */
--color-studio-info: #3B82F6       /* 信息/主操作 */

/* 字体 */
--font-sans: 'Inter', system-ui, sans-serif
--font-mono: 'JetBrains Mono', monospace
```
