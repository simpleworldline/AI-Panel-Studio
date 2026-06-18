# 集成测试文档 (TDD: API + WebSocket + Services)

> **阶段**: TDD — RED  
> **日期**: 2026-06-18  
> **被测模块**: `app/services/` + `app/api/`  
> **依据文档**: API_CONTRACT.md, BACKEND_STRUCTURE.md

---

## 1. 测试范围

| 被测对象 | 端点/方法 | 设计文档 |
|----------|----------|----------|
| DiscussionService | create/list/detail/start/pause/resume/next/end | API_CONTRACT.md §2.1, §2.3 |
| PanelService | generate_panel/confirm_panel | API_CONTRACT.md §2.2 |
| ReportService | generate_report | API_CONTRACT.md §2.4 |
| WebSocket | ws_handler 连接/事件 | API_CONTRACT.md §3 |
| 全局错误处理 | 异常处理 | API_CONTRACT.md §1.4, §4 |

## 2. 核心测试用例

### Discussion API
- `test_create_discussion`: POST /api/discussions → 201 + 正确返回
- `test_create_discussion_invalid_topic`: 空话题 → 400
- `test_list_discussions`: GET /api/discussions → 分页列表
- `test_get_discussion_detail`: GET /api/discussions/{id} → 详情
- `test_start_discussion`: POST /start → status=live
- `test_pause_resume`: POST /pause + /resume 状态流转
- `test_end_discussion`: POST /end → status=ended
- `test_perm_denied`: 非创建者操作 → 403

---

## 3. 预期失败原因

路由未注册 → 所有 HTTP 请求返回 404
