# AI Panel Studio — 后端 API 接口文档

> **版本**: v1.0  
> **日期**: 2026-06-18  
> **框架**: FastAPI + SQLAlchemy 2.0 (async)  
> **Base URL**: `http://localhost:8000` (开发)  
> **LLM**: DeepSeek API (`deepseek-chat`)

---

## 1. 通用规范

### 1.1 响应格式

**成功**
```json
{"code": 200, "data": { ... }, "message": "success"}
```

**失败**
```json
{"code": 404, "data": null, "message": "错误描述"}
```

### 1.2 通用请求头

| Header | 说明 | 必填 |
|--------|------|------|
| Content-Type | `application/json` | ✅ |
| X-Session-Id | 创建者 Session ID | 控制类端点 ✅ |

### 1.3 HTTP 状态码

| Status | code | 说明 |
|--------|------|------|
| 200 | 200 | 成功 |
| 201 | 201 | 创建成功 |
| 400 | - | 请求格式错误 |
| 403 | - | 权限拒绝 |
| 404 | - | 资源不存在 |
| 409 | - | 状态冲突 |
| 422 | 422 | 参数校验失败 |
| 500 | 500 | 服务器错误 |

---

## 2. REST API 端点

### 2.1 健康检查

```
GET /api/health
```

**响应**
```json
{
  "code": 200,
  "data": {"status": "ok"},
  "message": "success"
}
```

---

### 2.2 创建讨论

创建新的圆桌讨论，状态初始为 `pending`。

```
POST /api/discussions
Content-Type: application/json
X-Session-Id: <session_id>
```

**请求体**

| 字段 | 类型 | 必填 | 默认 | 约束 | 说明 |
|------|------|------|------|------|------|
| topic | string | ✅ | - | 1-200字符 | 讨论话题 |
| expert_count | int | ❌ | 4 | 2-8 | 嘉宾人数 |
| max_rounds | int\|null | ❌ | null | - | 最大轮次，null=不限 |

**请求示例**
```json
{
  "topic": "AI是否应该具备自我意识？",
  "expert_count": 6,
  "max_rounds": 10
}
```

**响应** `201 Created`
```json
{
  "code": 201,
  "data": {
    "id": "b7a6abed-3e00-4ec0-8fb5-d15bba71d1b6",
    "topic": "AI是否应该具备自我意识？",
    "expert_count": 6,
    "max_rounds": 10,
    "status": "pending",
    "creator_session_id": "sid-xxx",
    "current_round": 0,
    "created_at": "2026-06-18T10:30:00Z"
  },
  "message": "讨论创建成功"
}
```

**后端实现**
```python
# app/api/discussions.py
@router.post("", status_code=201)
async def create_discussion(body: DiscussionCreate, x_session_id: str = Header(...), db = Depends(get_db)):
    d = await DiscussionService.create(db, topic=body.topic, creator_session_id=x_session_id,
                                        expert_count=body.expert_count, max_rounds=body.max_rounds)
    return ApiResponse(code=201, data={...}, message="讨论创建成功")

# app/services/discussion_service.py
class DiscussionService:
    @staticmethod
    async def create(session, topic, creator_session_id, expert_count=4, max_rounds=None) -> Discussion:
        d = Discussion(id=str(uuid.uuid4()), topic=topic, expert_count=expert_count,
                       max_rounds=max_rounds, creator_session_id=creator_session_id)
        session.add(d); await session.flush(); await session.refresh(d)
        return d
```

**错误**
| code | 说明 |
|------|------|
| 422 | topic 为空或超过 200 字 |
| 422 | expert_count 不在 2-8 |

---

### 2.3 讨论列表

按状态筛选并分页获取讨论列表。

```
GET /api/discussions?status=live&page=1&page_size=20
```

**Query 参数**

| 参数 | 类型 | 必填 | 默认 | 约束 | 说明 |
|------|------|------|------|------|------|
| status | string | ❌ | - | `live`/`pending`/`ended` | 不传=全部 |
| page | int | ❌ | 1 | ≥1 | 页码 |
| page_size | int | ❌ | 20 | 1-100 | 每页数量 |

**响应** `200`
```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": "uuid",
        "topic": "AI是否应该具备自我意识？",
        "expert_count": 4,
        "status": "live",
        "current_round": 5,
        "created_at": "2026-06-17T10:00:00Z",
        "member_preview": [
          {"name": "张明", "role": "host"},
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

**后端实现**: `DiscussionService.list_discussions()` — 联表查询 PanelMember 生成 member_preview，分页返回。

---

### 2.4 讨论详情

获取单个讨论的完整信息：嘉宾阵容 + 发言记录 + 共识/分歧。

```
GET /api/discussions/{discussion_id}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| discussion_id | string | 讨论 UUID |

**响应** `200`
```json
{
  "code": 200,
  "data": {
    "id": "uuid",
    "topic": "AI是否应该具备自我意识？",
    "expert_count": 4,
    "status": "live",
    "current_round": 5,
    "max_rounds": null,
    "created_at": "2026-06-17T10:00:00Z",
    "ended_at": null,
    "creator_session_id": "sid-xxx",
    "panel": [
      {
        "id": "pm-uuid-1",
        "name": "张明",
        "title": "AI伦理学家",
        "role": "host",
        "stance": "中立客观",
        "color": "#6366F1"
      }
    ],
    "transcript": [
      {
        "id": "u-uuid-1",
        "panel_member_id": "pm-uuid-1",
        "member_name": "张明",
        "member_title": "AI伦理学家",
        "member_color": "#6366F1",
        "content": "今天我们讨论...",
        "utterance_type": "opening",
        "sequence_num": 1,
        "round_num": 0,
        "created_at": "2026-06-17T10:01:00Z"
      }
    ],
    "consensus": [
      {
        "id": "cd-uuid-1",
        "type": "consensus",
        "title": "共识标题",
        "description": "双方均认同...",
        "source_utterance_ids": ["u-1", "u-5"],
        "confidence": 0.92,
        "is_resolved": false,
        "round_num": 2
      }
    ],
    "disagreements": [ ... ]
  },
  "message": "success"
}
```

**面板成员字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 嘉宾 UUID |
| name | string | 姓名 ≤50字 |
| title | string | 职业/Title ≤100字 |
| role | string | `host` 或 `expert` |
| stance | string | 立场描述 ≤200字 |
| color | string | HEX 颜色 #RRGGBB |

**发言字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 发言 UUID |
| panel_member_id | string | 发言人 ID |
| member_name | string | 发言人姓名 |
| member_title | string | 发言人职业 |
| member_color | string | 发言人颜色 |
| content | string | 发言正文 |
| utterance_type | string | opening/statement/rebuttal/supplement/question/summary |
| sequence_num | int | 全局序号递增 |
| round_num | int | 所属轮次 0=开场 |
| created_at | string | ISO 8601 时间 |

**共识/分歧字段**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 记录 UUID |
| type | string | `consensus` 或 `disagreement` |
| title | string | 简短标题 ≤200字 |
| description | string | 详细说明 ≤1000字 |
| source_utterance_ids | string[] | 涉及的发言 ID 列表 |
| confidence | float | 置信度 0.0-1.0 |
| is_resolved | bool | 分歧是否已化解 |
| round_num | int | 产生时的轮次 |

**后端实现**: `DiscussionService.get_detail()` — 使用 `selectinload` eager load panel_members, utterances+panel_member, consensus_disagreements。

---

### 2.5 生成嘉宾阵容

调用 DeepSeek API LLM 根据话题实时生成 1 位主持人 + N 位嘉宾。

```
POST /api/discussions/{discussion_id}/panel/generate
Content-Type: application/json
```

**请求体**

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| regenerate_member_id | string\|null | ❌ | null | 指定重生某位嘉宾的 ID，null=全部生成 |

**请求示例**
```json
{
  "regenerate_member_id": null
}
```

**响应** `200`
```json
{
  "code": 200,
  "data": {
    "host": {
      "name": "张明",
      "title": "AI伦理学家",
      "stance": "中立客观，擅长引导讨论",
      "color": "#6366F1",
      "avatar_prompt": null
    },
    "experts": [
      {
        "name": "李研究员",
        "title": "认知科学研究所高级研究员",
        "stance": "支持AI具备有限自我意识",
        "color": "#EF4444",
        "avatar_prompt": null
      }
    ]
  },
  "message": "嘉宾阵容生成成功"
}
```

**后端实现**: `PanelService.generate_panel()` → 构建中文 Prompt → `llm_client.chat()` → 解析 JSON → 分配颜色。

**LLM Prompt**
```
系统: 你是一位专业的圆桌讨论策划人。根据用户给定的话题和专家人数，生成完整的嘉宾阵容...
用户: 话题：「AI是否应该具备自我意识？」\n需要的专家人数：4 位
```

**Fallback**: LLM 失败（网络错误/返回非法 JSON）时自动降级到 8 人 mock 中文阵容。

---

### 2.6 确认嘉宾阵容

用户编辑后确认阵容，写入数据库。**一经确认不可修改。**

```
PUT /api/discussions/{discussion_id}/panel
Content-Type: application/json
X-Session-Id: <session_id>
```

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

**请求示例**
```json
{
  "host": {"name": "张明", "title": "AI伦理学家", "stance": "中立客观", "color": "#6366F1"},
  "experts": [
    {"name": "李研究员", "title": "认知科学", "stance": "支持", "color": "#EF4444"},
    {"name": "王教授", "title": "哲学家", "stance": "反对", "color": "#10B981"}
  ]
}
```

**响应** `200`
```json
{
  "code": 200,
  "data": {
    "discussion_id": "uuid",
    "panel_confirmed": true,
    "members": [
      {"id": "pm-1", "name": "张明", "title": "AI伦理学家", "role": "host", "stance": "中立客观", "color": "#6366F1"},
      {"id": "pm-2", "name": "李研究员", "title": "认知科学", "role": "expert", "stance": "支持", "color": "#EF4444"}
    ]
  },
  "message": "嘉宾阵容确认成功"
}
```

**后端实现**: `PanelService.confirm_panel()` → 检查是否已确认 → 清除旧阵容 → 写入 PanelMember 表。

**错误**
| code | 说明 |
|------|------|
| 404 | 讨论不存在 |
| 409 | 阵容已确认不可修改 |
| 422 | 字段校验失败 |

---

### 2.7 开始讨论

将讨论状态从 `pending` 改为 `live`，并启动后台 DiscussionRunner 执行 LLM 驱动的 Agent 发言循环。

```
POST /api/discussions/{discussion_id}/start
X-Session-Id: <session_id>
```

**请求体**: 无

**响应** `200`
```json
{
  "code": 200,
  "data": {"discussion_id": "uuid", "status": "live"},
  "message": "讨论已开始"
}
```

**后台行为**:
1. 创建 `DiscussionRunner` 实例并注册到全局 `RunnerRegistry`
2. `asyncio.create_task(runner.run())` 启动异步发言循环
3. Runner: 开场白 → Agent 欲望值计算 → Scheduler 选发言者 → LLM 流式生成 → Observer 分析 → 下一轮...

**错误**
| code | 说明 |
|------|------|
| 403 | 非创建者无权操作 |
| 409 | 阵容未确认 / 讨论已结束 |

---

### 2.8 暂停讨论

```
POST /api/discussions/{discussion_id}/pause
X-Session-Id: <session_id>
```

**请求体**: 无

**响应** `200`
```json
{
  "code": 200,
  "data": {"discussion_id": "uuid", "status": "paused"},
  "message": "讨论已暂停"
}
```

**Runner 行为**: `runner.pause()` → asyncio.Event.clear() 阻塞发言循环。

---

### 2.9 继续讨论

```
POST /api/discussions/{discussion_id}/resume
X-Session-Id: <session_id>
```

**请求体**: 无

**响应** `200`
```json
{
  "code": 200,
  "data": {"discussion_id": "uuid", "status": "live"},
  "message": "讨论已继续"
}
```

**Runner 行为**: `runner.resume()` → asyncio.Event.set() 恢复发言循环。

---

### 2.10 手动推进下一轮

```
POST /api/discussions/{discussion_id}/next
X-Session-Id: <session_id>
```

**请求体**: 无

**响应** `200`
```json
{
  "code": 200,
  "data": {"discussion_id": "uuid", "round_triggered": true},
  "message": "已触发下一轮发言"
}
```

**Runner 行为**: `runner.resume()` 触发一轮发言循环迭代。

---

### 2.11 强制结束讨论

结束讨论，Runner 生成主持人总结后停止。

```
POST /api/discussions/{discussion_id}/end
X-Session-Id: <session_id>
```

**请求体**: 无

**响应** `200`
```json
{
  "code": 200,
  "data": {
    "discussion_id": "uuid",
    "status": "ended",
    "ended_at": "2026-06-17T10:30:00Z",
    "total_rounds": 12,
    "total_utterances": 28
  },
  "message": "讨论已结束"
}
```

**Runner 行为**: `await runner.stop()` → 生成主持人总结 → 广播 `discussion_ended`。

---

### 2.12 讨论报告

获取讨论的完整报告：Transcript + 共识/分歧 + 主持人总结。

```
GET /api/discussions/{discussion_id}/report
```

**响应** `200`
```json
{
  "code": 200,
  "data": {
    "discussion_id": "uuid",
    "topic": "AI是否应该具备自我意识？",
    "panel": [ ... ],
    "transcript": [
      {
        "id": "u-1",
        "panel_member_id": "pm-1",
        "member_name": "张明",
        "member_title": "AI伦理学家",
        "member_color": "#6366F1",
        "content": "今天我们讨论...",
        "utterance_type": "opening",
        "sequence_num": 1,
        "round_num": 0,
        "created_at": "2026-06-17T10:01:00Z"
      }
    ],
    "consensus": [
      {"id": "cd-1", "type": "consensus", "title": "...", "description": "...",
       "source_utterance_ids": ["u-1","u-3"], "confidence": 0.9, "is_resolved": false, "round_num": 2}
    ],
    "disagreements": [
      {"id": "cd-2", "type": "disagreement", "title": "...", "description": "...",
       "source_utterance_ids": ["u-2"], "confidence": 0.8, "is_resolved": true, "round_num": 1}
    ],
    "host_summary": "今天的讨论非常精彩..."

  },
  "message": "success"
}
```

**后端实现**: `ReportService.generate_report()` — 聚合查询 PanelMember + Utterance(含 panel_member eager load) + ConsensusDisagreement。

---

## 3. WebSocket 实时通信

### 3.1 连接

```
ws://localhost:8000/ws/discussions/{discussion_id}?session_id=<session_id>
```

**连接流程**:
1. 验证讨论存在 → 不存在则 close(4004)
2. 接受连接 → 注册到 ConnectionManager
3. 创建者 session_id 匹配 → `is_creator=true` 可发送控制指令
4. 观看者 → 仅接收事件

### 3.2 客户端 → 服务端

| type | 说明 | 权限 |
|------|------|------|
| `{"type":"advance"}` | 推进下一轮 | 创建者 |
| `{"type":"pause"}` | 暂停讨论 | 创建者 |
| `{"type":"resume"}` | 继续讨论 | 创建者 |
| `{"type":"end"}` | 强制结束 | 创建者 |

### 3.3 服务端 → 客户端

#### expert_status — 专家状态变更

```json
{
  "type": "expert_status",
  "data": {
    "member_id": "pm-uuid",
    "member_name": "李研究员",
    "member_color": "#EF4444",
    "status": "preparing",
    "focus_summary": "正在思考AI边界问题",
    "desire_value": 0.85,
    "timestamp": "2026-06-17T10:05:01Z"
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| member_id | string | 嘉宾 ID |
| member_name | string | 姓名 |
| member_color | string | 颜色 |
| status | string | `idle` / `preparing` / `speaking` |
| focus_summary | string\|null | 公开思考摘要 |
| desire_value | float | 发言欲望值 0.0-1.0 |
| timestamp | string | ISO 8601 |

#### utterance_token — 流式发言逐 token

```json
{
  "type": "utterance_token",
  "data": {
    "utterance_id": "u-uuid",
    "member_id": "pm-uuid",
    "member_name": "李研究员",
    "member_title": "认知科学家",
    "member_color": "#EF4444",
    "token": "我认为",
    "sequence_num": 5,
    "round_num": 2,
    "is_first": false,
    "is_last": false
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| utterance_id | string | 发言 ID |
| token | string | 增量文本 |
| is_first | bool | 该发言首个 token |
| is_last | bool | 该发言最后 token |

#### utterance_complete — 发言完成

```json
{
  "type": "utterance_complete",
  "data": {
    "utterance_id": "u-uuid",
    "member_id": "pm-uuid",
    "member_name": "李研究员",
    "member_title": "认知科学家",
    "member_color": "#EF4444",
    "content": "完整发言内容...",
    "utterance_type": "statement",
    "sequence_num": 5,
    "round_num": 2,
    "created_at": "2026-06-17T10:05:05Z"
  }
}
```

#### consensus_update — 共识/分歧更新

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
      "source_utterance_ids": ["u-1", "u-5"],
      "confidence": 0.92,
      "is_resolved": false,
      "round_num": 2
    }
  }
}
```

| action | 说明 |
|--------|------|
| `created` | 新共识/分歧 |
| `updated` | 已有记录更新 |
| `resolved` | 分歧被化解 |

#### discussion_paused / discussion_resumed

```json
{"type": "discussion_paused", "data": {"discussion_id": "uuid", "timestamp": "..."}}
{"type": "discussion_resumed", "data": {"discussion_id": "uuid", "timestamp": "..."}}
```

#### discussion_ended

```json
{
  "type": "discussion_ended",
  "data": {
    "discussion_id": "uuid",
    "end_reason": "user_ended",
    "total_rounds": 12,
    "total_utterances": 28,
    "ended_at": "2026-06-17T10:30:00Z"
  }
}
```

| end_reason | 说明 |
|------------|------|
| `user_ended` | 用户手动结束 |
| `max_rounds` | 达到预设最大轮次 |
| `no_consensus` | 连续无新共识 |
| `host_decided` | 主持人自动结束 |

---

## 4. 架构总览

```
POST /start  ─→  DiscussionService.start()
                     │
                     ├── d.status = "live"
                     └── asyncio.create_task(runner.run())
                              │
                              ▼
                     DiscussionRunner (后台异步)
                       │
                       ├── 开场白 (HostAgent.generate_utterance)
                       │     └── llm_client.chat_stream() → token → WS broadcast
                       │
                       ├── 主循环 while running:
                       │   ├── pause.wait()  (asyncio.Event)
                       │   ├── 各 Agent.prepare() 计算 desire_value
                       │   ├── Scheduler.select_speaker()  决断链排序
                       │   ├── speaker.generate_utterance()  流式生成
                       │   │     └── WS: utterance_token* + utterance_complete
                       │   ├── Observer.analyze()  共识/分歧
                       │   │     └── WS: consensus_update
                       │   └── current_round++
                       │
                       └── 结束时
                             ├── HostAgent.generate_summary()
                             └── WS: discussion_ended
```

---

## 5. 模块映射

| 层 | 模块 | 职责 |
|----|------|------|
| API Routes | `api/discussions.py` | 12 个 REST 端点 |
| API Routes | `api/panel.py` | 2 个嘉宾端点 |
| API Routes | `api/ws.py` | WebSocket + ConnectionManager |
| Services | `services/discussion_service.py` | CRUD + 状态流转 + 权限 |
| Services | `services/panel_service.py` | LLM 生成 + 阵容确认 |
| Services | `services/report_service.py` | 报告聚合查询 |
| Services | `services/runner_registry.py` | Runner 全局注册表 |
| Agents | `agents/llm_client.py` | DeepSeek API (chat + stream) |
| Agents | `agents/base_agent.py` | Agent 抽象基类 |
| Agents | `agents/host_agent.py` | 主持人 (开场/提问/总结) |
| Agents | `agents/expert_agent.py` | 专家 (欲望值 + 发言) |
| Agents | `agents/observer_agent.py` | 观察员 (共识/分歧) |
| Agents | `agents/scheduler.py` | 欲望值排序仲裁 |
| Agents | `agents/discussion_runner.py` | 讨论生命周期引擎 |
| Models | `models/*.py` | 5 表 SQLAlchemy 模型 |
| Schemas | `schemas/*.py` | 6 模块 Pydantic 校验 |

## 6. 数据库表

| 表 | SQLAlchemy Model | 说明 |
|----|-----------------|------|
| discussions | Discussion | 讨论主体 |
| panel_members | PanelMember | 嘉宾/主持人 |
| utterances | Utterance | 发言记录 |
| consensus_disagreements | ConsensusDisagreement | 共识/分歧 |
| expert_status_logs | ExpertStatusLog | 状态变更日志 |

## 7. 测试覆盖

| 层级 | 文件 | 测试数 |
|------|------|--------|
| Unit — DB | test_database.py | 24 |
| Unit — Schema | test_schemas.py | 33 |
| Unit — Scheduler | test_scheduler.py | 6 |
| Unit — LLM Panel | test_llm_panel.py | 4 |
| Integration — API | test_discussion_api.py | 19 |
| Integration — Error | test_error_handling.py | 5 |
| E2E — Full Flow | test_full_user_flow.py | 25 |
| **合计** | | **116** |
