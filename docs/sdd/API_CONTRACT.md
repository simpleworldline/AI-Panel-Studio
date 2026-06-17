# AI Panel Studio — API 契约文档

> **阶段**: SDD  
> **日期**: 2026-06-17  
> **协议**: REST JSON + WebSocket (WSS)

---

## 1. 通用规范

### 1.1 Base URL

```
开发环境: http://localhost:8000
生产环境: https://<domain>
```

### 1.2 通用请求头

```
Content-Type: application/json
Accept: application/json
X-Session-Id: <creator_session_id>  # 讨论创建者身份标识
```

### 1.3 通用响应格式

**成功响应**:
```json
{
  "code": 200,
  "data": { ... },
  "message": "success"
}
```

**错误响应**:
```json
{
  "code": 400,
  "data": null,
  "message": "话题长度不能超过200字",
  "detail": "validation_error"
}
```

### 1.4 HTTP 状态码规范

| 状态码 | 含义 | 场景 |
|--------|------|------|
| 200 | 成功 | 正常响应 |
| 201 | 创建成功 | POST 新建资源 |
| 400 | 请求参数错误 | 校验失败 |
| 403 | 无权限 | 非创建者尝试控制讨论 |
| 404 | 资源不存在 | 讨论/嘉宾 ID 无效 |
| 409 | 状态冲突 | 对已结束讨论执行操作 |
| 422 | 业务逻辑错误 | 如：阵容未确认即开始讨论 |
| 500 | 服务器内部错误 | LLM API 异常等 |

---

## 2. REST API 端点

### 2.1 讨论管理

#### `POST /api/discussions` — 创建讨论

```
Request:
{
  "topic": "AI是否应该具备自我意识？",       // string, 1-200字
  "expert_count": 4,                        // int, 2-8, default 4
  "max_rounds": null                        // int|null, nullable=不限
}

Response 201:
{
  "code": 201,
  "data": {
    "id": "uuid-4",
    "topic": "AI是否应该具备自我意识？",
    "expert_count": 4,
    "max_rounds": null,
    "status": "pending",
    "creator_session_id": "session-xxx",
    "current_round": 0,
    "created_at": "2026-06-17T10:00:00Z"
  },
  "message": "讨论创建成功"
}
```

#### `GET /api/discussions` — 讨论列表

```
Query Parameters:
  status: "live" | "ended"                  // 可选，筛选状态
  page: 1                                   // 可选，分页页码
  page_size: 20                             // 可选，每页数量

Response 200:
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "uuid-4",
        "topic": "AI是否应该具备自我意识？",
        "expert_count": 4,
        "status": "live",
        "current_round": 5,
        "created_at": "2026-06-17T10:00:00Z",
        "member_preview": [
          {"name": "张教授", "role": "host"},
          {"name": "李研究员", "role": "expert"}
        ]
      }
    ],
    "total": 42,
    "page": 1,
    "page_size": 20
  },
  "message": "success"
}
```

#### `GET /api/discussions/{discussion_id}` — 讨论详情

```
Response 200:
{
  "code": 200,
  "data": {
    "id": "uuid-4",
    "topic": "AI是否应该具备自我意识？",
    "expert_count": 4,
    "status": "live",
    "current_round": 5,
    "max_rounds": null,
    "created_at": "2026-06-17T10:00:00Z",
    "ended_at": null,
    "panel": [
      {
        "id": "pm-uuid-1",
        "name": "张明",
        "title": "AI伦理学家",
        "role": "host",
        "stance": "中立客观，擅长引导讨论",
        "color": "#6366F1"
      },
      {
        "id": "pm-uuid-2",
        "name": "李研究员",
        "title": "认知科学研究所高级研究员",
        "role": "expert",
        "stance": "支持AI具备有限自我意识",
        "color": "#EF4444"
      }
    ],
    "transcript": [
      {
        "id": "u-uuid-1",
        "panel_member_id": "pm-uuid-1",
        "member_name": "张明",
        "member_title": "AI伦理学家",
        "member_color": "#6366F1",
        "content": "今天我们讨论一个非常前沿的话题...",
        "utterance_type": "opening",
        "sequence_num": 1,
        "round_num": 0,
        "created_at": "2026-06-17T10:01:00Z"
      }
    ],
    "consensus": [...],
    "disagreements": [...]
  },
  "message": "success"
}
```

---

### 2.2 嘉宾阵容

#### `POST /api/discussions/{discussion_id}/panel/generate` — LLM 生成嘉宾建议

```
Request:
{
  "regenerate_member_id": null              // string|null, 单个重生时指定
}

Response 200:
{
  "code": 200,
  "data": {
    "host": {
      "name": "张明",
      "title": "AI伦理学家",
      "stance": "中立客观，擅长引导讨论",
      "color": "#6366F1",
      "avatar_prompt": "一位40岁的中国男性学者..."
    },
    "experts": [
      {
        "name": "李研究员",
        "title": "认知科学研究所高级研究员",
        "stance": "支持AI具备有限自我意识",
        "color": "#EF4444",
        "avatar_prompt": "..."
      }
    ]
  },
  "message": "嘉宾阵容生成成功"
}
```

#### `PUT /api/discussions/{discussion_id}/panel` — 编辑并确认阵容

```
Request:
{
  "host": {
    "name": "张明（已编辑）",
    "title": "AI伦理学家",
    "stance": "中立客观",
    "color": "#6366F1"
  },
  "experts": [
    {
      "name": "李研究员",
      "title": "认知科学研究所高级研究员",
      "stance": "支持AI具备有限自我意识",
      "color": "#EF4444"
    }
  ]
}

Response 200:
{
  "code": 200,
  "data": {
    "discussion_id": "uuid-4",
    "panel_confirmed": true,
    "members": [...]
  },
  "message": "嘉宾阵容确认成功"
}
```

---

### 2.3 讨论控制

#### `POST /api/discussions/{discussion_id}/start` — 开始讨论

```
Request: (空体)
Response 200:
{
  "code": 200,
  "data": {
    "discussion_id": "uuid-4",
    "status": "live"
  },
  "message": "讨论已开始"
}
```

#### `POST /api/discussions/{discussion_id}/pause` — 暂停讨论

```
Request: (空体)
Response 200:
{
  "code": 200,
  "data": { "discussion_id": "uuid-4", "status": "paused" },
  "message": "讨论已暂停"
}
```

#### `POST /api/discussions/{discussion_id}/resume` — 继续讨论

```
Request: (空体)
Response 200:
{
  "code": 200,
  "data": { "discussion_id": "uuid-4", "status": "live" },
  "message": "讨论已继续"
}
```

#### `POST /api/discussions/{discussion_id}/next` — 手动推进下一轮

```
Request: (空体)
Response 200:
{
  "code": 200,
  "data": { "discussion_id": "uuid-4", "round_triggered": true },
  "message": "已触发下一轮发言"
}
```

#### `POST /api/discussions/{discussion_id}/end` — 强制结束

```
Request: (空体)
Response 200:
{
  "code": 200,
  "data": {
    "discussion_id": "uuid-4",
    "status": "ended",
    "ended_at": "2026-06-17T10:30:00Z",
    "total_rounds": 12,
    "total_utterances": 28
  },
  "message": "讨论已结束"
}
```

---

### 2.4 讨论报告

#### `GET /api/discussions/{discussion_id}/report` — 讨论总结报告

```
Response 200:
{
  "code": 200,
  "data": {
    "discussion_id": "uuid-4",
    "topic": "AI是否应该具备自我意识？",
    "panel": [...],
    "transcript": [
      {
        "sequence_num": 1,
        "member_name": "张明",
        "member_title": "AI伦理学家",
        "member_color": "#6366F1",
        "content": "...",
        "utterance_type": "opening"
      }
    ],
    "consensus": [...],
    "disagreements": [...],
    "host_summary": "今天的讨论非常精彩..."   // 主持人总结（最后一条发言）
  },
  "message": "success"
}
```

---

## 3. WebSocket 事件协议

### 3.1 连接

```
URL: ws://localhost:8000/ws/discussions/{discussion_id}
Query: ?session_id=<creator_session_id>
```

连接建立后，服务端推送初始状态快照，随后发送增量事件。

### 3.2 服务端 → 客户端事件

#### `expert_status` — 专家状态变更

```json
{
  "type": "expert_status",
  "data": {
    "member_id": "pm-uuid-2",
    "member_name": "李研究员",
    "member_color": "#EF4444",
    "status": "preparing",                // idle | preparing | speaking
    "focus_summary": "正在思考张教授关于AI边界的观点",
    "desire_value": 0.85,
    "timestamp": "2026-06-17T10:05:01Z"
  }
}
```

#### `utterance_token` — 发言流式 Token

```json
{
  "type": "utterance_token",
  "data": {
    "utterance_id": "u-uuid-5",
    "member_id": "pm-uuid-2",
    "member_name": "李研究员",
    "member_title": "认知科学研究所高级研究员",
    "member_color": "#EF4444",
    "token": "我认为",                      // 增量文本
    "sequence_num": 5,
    "round_num": 2,
    "is_first": false,                     // 该发言的首个 token
    "is_last": false                       // 该发言的最后一个 token
  }
}
```

#### `utterance_complete` — 发言完成

```json
{
  "type": "utterance_complete",
  "data": {
    "utterance_id": "u-uuid-5",
    "member_id": "pm-uuid-2",
    "member_name": "李研究员",
    "member_title": "认知科学研究所高级研究员",
    "member_color": "#EF4444",
    "content": "我认为AI的自我意识应该从功能层面而非哲学层面来理解...",
    "utterance_type": "statement",
    "sequence_num": 5,
    "round_num": 2,
    "created_at": "2026-06-17T10:05:05Z"
  }
}
```

#### `consensus_update` — 共识/分歧更新

```json
{
  "type": "consensus_update",
  "data": {
    "action": "created",                   // created | updated | resolved
    "record": {
      "id": "cd-uuid-1",
      "type": "consensus",                 // consensus | disagreement
      "title": "AI自我意识定义共识",
      "description": "李研究员和王博士均认同应从功能层面定义AI自我意识",
      "source_utterance_ids": ["u-uuid-5", "u-uuid-2"],
      "confidence": 0.92,
      "round_num": 2
    }
  }
}
```

#### `discussion_paused` / `discussion_resumed` — 控制状态变更

```json
{
  "type": "discussion_paused",
  "data": {
    "discussion_id": "uuid-4",
    "timestamp": "2026-06-17T10:10:00Z"
  }
}
```

#### `discussion_ended` — 讨论结束

```json
{
  "type": "discussion_ended",
  "data": {
    "discussion_id": "uuid-4",
    "end_reason": "user_ended",            // user_ended | max_rounds | no_consensus | host_decided
    "total_rounds": 12,
    "total_utterances": 28,
    "ended_at": "2026-06-17T10:30:00Z"
  }
}
```

#### `discussion_control` — 面板状态变更（S→C）

```json
{
  "type": "discussion_control",
  "data": {
    "action": "max_rounds_reached",
    "message": "已达到预设最大轮次，讨论即将结束"
  }
}
```

### 3.3 客户端 → 服务端事件

```json
// 手动推进
{ "type": "advance" }

// 暂停
{ "type": "pause" }

// 继续
{ "type": "resume" }

// 强制结束
{ "type": "end" }
```

---

## 4. 错误码汇总

| 错误码 | 名称 | 说明 |
|--------|------|------|
| 40001 | INVALID_TOPIC | 话题为空或超过200字 |
| 40002 | INVALID_EXPERT_COUNT | 专家人数不在2-8范围内 |
| 40003 | INVALID_PANEL | 阵容数据不完整或字段非法 |
| 40004 | INVALID_MEMBER_COLOR | 颜色格式错误 |
| 40401 | DISCUSSION_NOT_FOUND | 讨论不存在 |
| 40402 | MEMBER_NOT_FOUND | 嘉宾不存在 |
| 40301 | NOT_CREATOR | 非创建者无权操作 |
| 40901 | ALREADY_ENDED | 讨论已结束不可操作 |
| 40902 | NOT_LIVE | 讨论不在直播状态 |
| 40903 | PANEL_ALREADY_CONFIRMED | 阵容已确认不可修改 |
| 42201 | PANEL_NOT_CONFIRMED | 阵容未确认无法开始讨论 |
| 50001 | LLM_API_ERROR | DeepSeek API 调用失败 |
| 50002 | AGENT_ERROR | Agent 调度异常 |

---

## 5. 权限校验矩阵

| 操作 | 创建者 | 观看者（其他 Session） |
|------|--------|------------------------|
| 创建/编辑阵容/开始/暂停/继续/结束/推进 | ✅ | ❌ 40301 |
| 查看讨论详情/Transcript | ✅ | ✅ |
| 查看报告 | ✅ | ✅ |
| WebSocket 连接 | ✅ 可发控制指令 | ✅ 仅接收 |
