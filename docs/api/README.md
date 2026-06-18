# AI Panel Studio — 前端 API 接口文档

> **版本**: v1.0  
> **日期**: 2026-06-18  
> **Base URL**: `http://localhost:8000/api` (开发) / `https://<domain>/api` (生产)  
> **通用请求头**: `Content-Type: application/json`, `X-Session-Id: <creator_session_id>`

---

## 通用响应格式

### 成功
```json
{"code": 200, "data": { ... }, "message": "success"}
```

### 失败
```json
{"code": 400, "data": null, "message": "错误描述"}
```

### 分页列表
```json
{
  "code": 200,
  "data": {
    "items": [ ... ],
    "total": 42,
    "page": 1,
    "pageSize": 20
  },
  "message": "success"
}
```

---

## 1. 讨论管理 API

### 1.1 创建讨论

创建新的圆桌讨论。

```
POST /api/discussions
```

**请求头**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| X-Session-Id | string | ✅ | 创建者 Session 标识 |

**请求体**
| 字段 | 类型 | 必填 | 默认 | 约束 | 说明 |
|------|------|------|------|------|------|
| topic | string | ✅ | - | 1-200字 | 讨论话题 |
| expertCount | number | ❌ | 4 | 2-8 | 嘉宾人数 |
| maxRounds | number\|null | ❌ | null | - | 最大轮次，null=不限 |

**响应体** `code=201`
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 讨论唯一标识 UUID |
| topic | string | 讨论话题 |
| expertCount | number | 嘉宾人数 |
| maxRounds | number\|null | 最大轮次 |
| status | string | `pending` — 待开始 |
| creatorSessionId | string | 创建者 Session |
| currentRound | number | 当前轮次 初始=0 |
| createdAt | string | ISO 8601 创建时间 |

**错误码**
| code | 说明 |
|------|------|
| 422 | 话题为空或超200字 / expertCount不在2-8 |

**前端调用**
```typescript
import { createDiscussion } from '../api/discussions';
const res = await createDiscussion({ topic: 'AI是否具备自我意识？', expertCount: 6 });
// res.data.id → discussionId
```

---

### 1.2 讨论列表

获取讨论列表，支持按状态筛选和分页。

```
GET /api/discussions?status=live&page=1&pageSize=20
```

**Query 参数**
| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| status | string | ❌ | - | `live` / `pending` / `ended`，不传=全部 |
| page | number | ❌ | 1 | 页码 ≥1 |
| pageSize | number | ❌ | 20 | 每页数量 1-100 |

**响应体** `code=200`
| 字段 | 类型 | 说明 |
|------|------|------|
| items | DiscussionSummary[] | 讨论摘要列表 |
| total | number | 总数 |
| page | number | 当前页码 |
| pageSize | number | 每页数量 |

**DiscussionSummary 结构**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 讨论ID |
| topic | string | 话题 |
| expertCount | number | 嘉宾人数 |
| status | string | live / pending / ended |
| currentRound | number | 当前轮次 |
| createdAt | string | 创建时间 |
| memberPreview | object[] | 前2位嘉宾 {name, role} |

**前端调用**
```typescript
import { fetchDiscussions } from '../api/discussions';
const res = await fetchDiscussions('live');           // 进行中
const res = await fetchDiscussions('pending');         // 待开始
const res = await fetchDiscussions('ended');           // 已结束
const res = await fetchDiscussions(undefined, 1, 50);  // 全部
```

---

### 1.3 讨论详情

获取单个讨论的完整信息，含嘉宾阵容、发言记录、共识/分歧。

```
GET /api/discussions/:discussionId
```

**路径参数**
| 字段 | 类型 | 说明 |
|------|------|------|
| discussionId | string | 讨论UUID |

**响应体** `code=200`
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 讨论ID |
| topic | string | 话题 |
| expertCount | number | 嘉宾人数 |
| status | string | pending / live / paused / ended |
| currentRound | number | 当前轮次 |
| maxRounds | number\|null | 最大轮次 |
| createdAt | string | 创建时间 |
| endedAt | string\|null | 结束时间 |
| creatorSessionId | string | 创建者Session |
| panel | PanelMember[] | 完整嘉宾阵容 |
| transcript | Utterance[] | 发言记录 |
| consensus | Consensus[] | 共识列表 |
| disagreements | Consensus[] | 分歧列表 |

**PanelMember 结构**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 嘉宾ID |
| name | string | 姓名 |
| title | string | 职业/Title |
| role | string | host / expert |
| stance | string | 立场描述 |
| color | string | 专属HEX颜色 #RRGGBB |

**Utterance 结构**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 发言ID |
| panelMemberId | string | 发言人ID |
| memberName | string | 发言人姓名 |
| memberTitle | string | 发言人职业 |
| memberColor | string | 发言人颜色 |
| content | string | 发言内容 |
| utteranceType | string | opening/statement/rebuttal/supplement/question/summary |
| sequenceNum | number | 全局序号 |
| roundNum | number | 所属轮次 |
| createdAt | string | 创建时间 |

**Consensus 结构**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 记录ID |
| type | string | consensus / disagreement |
| title | string | 简短标题 |
| description | string | 详细说明 |
| sourceUtteranceIds | string[] | 涉及的发言ID |
| confidence | number | 置信度 0.0-1.0 |
| isResolved | boolean | 分歧是否已化解 |
| roundNum | number | 产生轮次 |

**前端调用**
```typescript
import { fetchDiscussionDetail } from '../api/discussions';
const res = await fetchDiscussionDetail(discussionId);
// res.data.panel → 嘉宾列表
// res.data.transcript → 发言记录
```

---

## 2. 嘉宾阵容 API

### 2.1 生成嘉宾阵容

调用 LLM 根据话题生成 1 位主持人 + N 位嘉宾。

```
POST /api/discussions/:discussionId/panel/generate
```

**请求体**
| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| regenerateMemberId | string\|null | ❌ | null | 指定重生某位嘉宾ID，null=全部生成 |

**响应体** `code=200`
| 字段 | 类型 | 说明 |
|------|------|------|
| host | MemberGenerateItem | 主持人 |
| experts | MemberGenerateItem[] | 嘉宾列表（数量=expertCount） |

**MemberGenerateItem 结构**
| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 姓名 |
| title | string | 职业/Title |
| stance | string | 立场描述 |
| color | string | HEX颜色 |
| avatarPrompt | string\|null | 头像提示词（v1.1预留） |

**实现说明**: 调用 DeepSeek API 实时生成中文阵容。LLM 失败时自动 fallback 到 8 人 mock 数据。

**错误码**
| code | 说明 |
|------|------|
| 404 | 讨论不存在 |

**前端调用**
```typescript
import { generatePanel } from '../api/panel';
const res = await generatePanel(discussionId, { regenerateMemberId: null });
// res.data.host → 主持人
// res.data.experts → 嘉宾列表
```

---

### 2.2 确认阵容

用户编辑后确认嘉宾阵容，写入数据库。确认后不可再修改。

```
PUT /api/discussions/:discussionId/panel
```

**请求头**
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| X-Session-Id | string | ✅ | 创建者 Session |

**请求体**
| 字段 | 类型 | 必填 | 约束 | 说明 |
|------|------|------|------|------|
| host.name | string | ✅ | 1-50字 | 主持人姓名 |
| host.title | string | ✅ | 1-100字 | 主持人职业 |
| host.stance | string | ✅ | 1-200字 | 主持人立场 |
| host.color | string | ✅ | #RRGGBB | 主持人颜色 |
| experts[].name | string | ✅ | 1-50字 | 嘉宾姓名 |
| experts[].title | string | ✅ | 1-100字 | 嘉宾职业 |
| experts[].stance | string | ✅ | 1-200字 | 嘉宾立场 |
| experts[].color | string | ✅ | #RRGGBB | 嘉宾颜色 |

**响应体** `code=200`
| 字段 | 类型 | 说明 |
|------|------|------|
| discussionId | string | 讨论ID |
| panelConfirmed | boolean | true=已确认 |
| members | PanelMember[] | 保存后的完整嘉宾列表 |

**错误码**
| code | 说明 |
|------|------|
| 409 | 阵容已确认不可修改 |
| 422 | 字段校验失败 |

**前端调用**
```typescript
import { confirmPanel } from '../api/panel';
const res = await confirmPanel(discussionId, {
  host: { name: '张明', title: 'AI专家', stance: '中立', color: '#6366F1' },
  experts: [{ name: '李四', title: '研究员', stance: '支持', color: '#EF4444' }],
});
// res.data.members → 已确认的嘉宾列表
```

---

## 3. 讨论控制 API

> **权限**: 以下所有端点仅创建者可操作，否则返回 403

### 3.1 开始讨论

```
POST /api/discussions/:discussionId/start
```

**请求头**: `X-Session-Id` ✅

**响应体** `code=200`
```json
{"code": 200, "data": {"discussionId": "...", "status": "live"}, "message": "讨论已开始"}
```

**错误码**: 403 非创建者, 409 阵容未确认/已结束

**前端调用**
```typescript
import { startDiscussion } from '../api/discussions';
await startDiscussion(discussionId);
```

---

### 3.2 暂停讨论

```
POST /api/discussions/:discussionId/pause
```

**请求头**: `X-Session-Id` ✅

**响应体** `code=200`
```json
{"code": 200, "data": {"discussionId": "...", "status": "paused"}, "message": "讨论已暂停"}
```

**错误码**: 403/409 (不在live状态)

**前端调用**
```typescript
import { pauseDiscussion } from '../api/discussions';
await pauseDiscussion(discussionId);
```

---

### 3.3 继续讨论

```
POST /api/discussions/:discussionId/resume
```

**请求头**: `X-Session-Id` ✅

**响应体** `code=200`
```json
{"code": 200, "data": {"discussionId": "...", "status": "live"}, "message": "讨论已继续"}
```

**错误码**: 403/409 (不在paused状态)

**前端调用**
```typescript
import { resumeDiscussion } from '../api/discussions';
await resumeDiscussion(discussionId);
```

---

### 3.4 手动推进下一轮

```
POST /api/discussions/:discussionId/next
```

**请求头**: `X-Session-Id` ✅

**响应体** `code=200`
```json
{"code": 200, "data": {"discussionId": "...", "roundTriggered": true}, "message": "已触发下一轮发言"}
```

**前端调用**
```typescript
import { advanceDiscussion } from '../api/discussions';
await advanceDiscussion(discussionId);
```

---

### 3.5 强制结束

```
POST /api/discussions/:discussionId/end
```

**请求头**: `X-Session-Id` ✅

**响应体** `code=200`
```json
{
  "code": 200,
  "data": {
    "discussionId": "...",
    "status": "ended",
    "endedAt": "2026-06-17T10:30:00Z",
    "totalRounds": 12,
    "totalUtterances": 28
  },
  "message": "讨论已结束"
}
```

**前端调用**
```typescript
import { endDiscussion } from '../api/discussions';
await endDiscussion(discussionId);
```

---

## 4. 讨论报告 API

### 4.1 获取报告

获取讨论的完整报告（Transcript + 共识/分歧 + 主持人总结）。

```
GET /api/discussions/:discussionId/report
```

**无需请求头** (任何人可查看)

**响应体** `code=200`
| 字段 | 类型 | 说明 |
|------|------|------|
| discussionId | string | 讨论ID |
| topic | string | 话题 |
| panel | PanelMember[] | 嘉宾阵容 |
| transcript | object[] | 发言记录 (sequenceNum/memberName/memberTitle/memberColor/content/utteranceType) |
| consensus | Consensus[] | 共识列表 |
| disagreements | Consensus[] | 分歧列表（含isResolved） |
| hostSummary | string | 主持人总结发言（最后一条summary类型发言，可能为空） |

**前端调用**
```typescript
import { fetchReport } from '../api/report';
const res = await fetchReport(discussionId);
// res.data.hostSummary → 主持人总结
// res.data.transcript → 完整发言
// res.data.consensus → 共识
// res.data.disagreements → 分歧
```

---

## 5. WebSocket 事件协议

### 5.1 连接

```
URL: ws://localhost:8000/ws/discussions/:discussionId?session_id=<sessionId>
```

**权限**: 创建者连接可发送控制指令，观看者连接仅接收

### 5.2 客户端 → 服务端

| type | 说明 | 权限 |
|------|------|------|
| `{"type":"advance"}` | 手动推进下一轮 | 创建者 |
| `{"type":"pause"}` | 暂停讨论 | 创建者 |
| `{"type":"resume"}` | 继续讨论 | 创建者 |
| `{"type":"end"}` | 强制结束 | 创建者 |

### 5.3 服务端 → 客户端

| type | 说明 | 触发时机 |
|------|------|----------|
| `expert_status` | 专家状态变更 | 每轮每位专家更新状态 |
| `utterance_token` | 发言流式token | 发言人逐字生成 |
| `utterance_complete` | 发言完成 | 每条发言结束时 |
| `consensus_update` | 共识/分歧更新 | 观察员分析后 |
| `discussion_paused` | 讨论已暂停 | 暂停时广播 |
| `discussion_resumed` | 讨论已继续 | 继续时广播 |
| `discussion_ended` | 讨论已结束 | 结束时广播 |
| `discussion_control` | 系统控制通知 | 自动结束等 |

#### expert_status
```json
{
  "type": "expert_status",
  "data": {
    "memberId": "pm-uuid",
    "memberName": "李研究员",
    "memberColor": "#EF4444",
    "status": "preparing",
    "focusSummary": "正在思考AI边界问题",
    "desireValue": 0.85,
    "timestamp": "2026-06-17T10:05:01Z"
  }
}
```

#### utterance_token
```json
{
  "type": "utterance_token",
  "data": {
    "utteranceId": "u-uuid",
    "memberId": "pm-uuid",
    "memberName": "李研究员",
    "memberTitle": "研究员",
    "memberColor": "#EF4444",
    "token": "我认为",
    "sequenceNum": 5,
    "roundNum": 2,
    "isFirst": false,
    "isLast": false
  }
}
```

#### utterance_complete
```json
{
  "type": "utterance_complete",
  "data": {
    "utteranceId": "u-uuid",
    "memberId": "pm-uuid",
    "memberName": "李研究员",
    "memberTitle": "研究员",
    "memberColor": "#EF4444",
    "content": "完整发言内容...",
    "utteranceType": "statement",
    "sequenceNum": 5,
    "roundNum": 2,
    "createdAt": "2026-06-17T10:05:05Z"
  }
}
```

#### consensus_update
```json
{
  "type": "consensus_update",
  "data": {
    "action": "created",
    "record": {
      "id": "cd-uuid",
      "type": "consensus",
      "title": "共识标题",
      "description": "详细说明",
      "sourceUtteranceIds": ["u-1", "u-5"],
      "confidence": 0.92,
      "isResolved": false,
      "roundNum": 2
    }
  }
}
```

#### discussion_ended
```json
{
  "type": "discussion_ended",
  "data": {
    "discussionId": "uuid",
    "endReason": "user_ended",
    "totalRounds": 12,
    "totalUtterances": 28,
    "endedAt": "2026-06-17T10:30:00Z"
  }
}
```

### 5.4 前端 WebSocket 调用

```typescript
import { StudioWebSocket } from '../ws/wsClient';

const handler = (event: WsServerEvent) => {
  // 处理各类事件
};
const ws = new StudioWebSocket(discussionId, sessionId, handler);
ws.connect();       // 连接
ws.send({ type: 'advance' });  // 发送控制指令
ws.close();         // 断开
```

---

## 6. 错误码汇总

| HTTP | code | 说明 |
|------|------|------|
| 400 | - | 请求格式错误 |
| 403 | - | 非创建者无权操作 |
| 404 | - | 讨论/资源不存在 |
| 409 | - | 状态冲突（已结束/已确认） |
| 422 | - | 参数校验失败 |
| 500 | - | 服务器内部错误 |

---

## 7. 前端 API 模块映射

| 模块 | 文件 | 导出函数 |
|------|------|----------|
| `api/client.ts` | HTTP客户端 | `apiClient` (axios instance) |
| `api/discussions.ts` | 讨论管理 | `createDiscussion`, `fetchDiscussions`, `fetchDiscussionDetail`, `startDiscussion`, `pauseDiscussion`, `resumeDiscussion`, `advanceDiscussion`, `endDiscussion`, `fetchDiscussionReport` |
| `api/panel.ts` | 嘉宾阵容 | `generatePanel`, `confirmPanel` |
| `api/report.ts` | 讨论报告 | `fetchReport` |
| `ws/wsClient.ts` | WebSocket | `StudioWebSocket` class |

---

## 8. 前端页面 ↔ API 调用关系

| 页面 | 调用的 API |
|------|-----------|
| HomePage | `fetchDiscussions(status)` |
| CreateDiscussionPage | `createDiscussion()` |
| PanelSetupPage | `generatePanel()`, `confirmPanel()` |
| StudioPage | `fetchDiscussionDetail()`, `startDiscussion()`, `pauseDiscussion()`, `resumeDiscussion()`, `advanceDiscussion()`, `endDiscussion()` |
| ReportPage | `fetchReport()` |
