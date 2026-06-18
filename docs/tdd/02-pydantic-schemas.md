# Pydantic Schemas 测试文档 (TDD: API Contracts)

> **阶段**: TDD — RED  
> **日期**: 2026-06-18  
> **被测模块**: `app/schemas/`  
> **依据文档**: API_CONTRACT.md, DATABASE_DESIGN.md

---

## 1. 测试范围

| 被测对象 | 文件 | 设计文档依据 |
|----------|------|-------------|
| 通用响应格式 | `app/schemas/common.py` | API_CONTRACT.md §1.3 |
| 讨论请求/响应 | `app/schemas/discussion.py` | API_CONTRACT.md §2.1 |
| 嘉宾阵容请求/响应 | `app/schemas/panel.py` | API_CONTRACT.md §2.2 |
| 发言响应 | `app/schemas/utterance.py` | API_CONTRACT.md §2.1 详情 |
| 共识/分歧响应 | `app/schemas/consensus.py` | API_CONTRACT.md §2.1 详情 |
| WebSocket 事件 | `app/schemas/ws_events.py` | API_CONTRACT.md §3 |

---

## 2. 测试用例

### 2.1 通用响应格式

| 测试名 | 验证点 |
|--------|--------|
| `test_api_response_success` | `ApiResponse` 包含 code/data/message，成功值正确 |
| `test_api_response_error` | `ApiResponse` 错误格式 code/data/message 正确 |
| `test_paginated_list` | `PaginatedList` 包含 items/total/page/page_size |

### 2.2 讨论 Schemas

| 测试名 | 验证点 |
|--------|--------|
| `test_discussion_create_valid` | 合法输入 → 验证通过 |
| `test_discussion_create_topic_empty` | 空话题 → ValidationError |
| `test_discussion_create_topic_too_long` | >200字话题 → ValidationError |
| `test_discussion_create_expert_count_range` | expert_count 2-8 通过，1和9拒绝 |
| `test_discussion_create_defaults` | expert_count 默认4 |
| `test_discussion_response_shape` | DiscussionResponse 包含 API_CONTRACT.md 指定所有字段 |
| `test_discussion_list_response_shape` | DiscussionList 分页格式正确 |

### 2.3 嘉宾阵容 Schemas

| 测试名 | 验证点 |
|--------|--------|
| `test_panel_member_response_shape` | MemberResponse 包含 name/title/role/stance/color |
| `test_panel_generate_request` | regenerate_member_id nullable |
| `test_panel_confirm_request_host_required` | host 必填 |
| `test_panel_confirm_request_experts_min` | experts 至少 1 位 |
| `test_panel_confirm_request_experts_max` | experts 最多 8 位 |

### 2.4 WebSocket 事件 Schema

| 测试名 | 验证点 |
|--------|--------|
| `test_ws_expert_status_event` | expert_status 事件结构与 API_CONTRACT.md §3.2 一致 |
| `test_ws_utterance_token_event` | utterance_token 包含 is_first/is_last |
| `test_ws_utterance_complete_event` | utterance_complete 包含完整字段 |
| `test_ws_consensus_update_event` | consensus_update 包含 action + record |
| `test_ws_discussion_ended_event` | ended 包含 end_reason 枚举 |
| `test_ws_client_events` | 客户端 4 个事件类型: advance/pause/resume/end |

---

## 3. 预期失败原因（RED 阶段）

`app/schemas/` 目录为空，所有导入将产生 ImportError。
