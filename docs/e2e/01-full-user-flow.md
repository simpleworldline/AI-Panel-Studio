# E2E-01～08: 完整用户流程测试

> **日期**: 2026-06-18  
> **方法**: 模拟用户从首页到报告的全流程，覆盖所有 API 端点和边界条件

---

## E2E-01: 创建讨论

| 测试名 | 操作 | 预期 |
|--------|------|------|
| `e2e_create_valid` | 话题="AI是否具备自我意识？", experts=6 | 201 + 返回完整字段 |
| `e2e_create_min` | 仅话题（默认值） | 201 + expertCount=4, status=pending |
| `e2e_create_empty_topic` | 话题="" | 422 |
| `e2e_create_topic_200` | 话题=200字 | 201 |
| `e2e_create_topic_201` | 话题=201字 | 422 |

## E2E-02: 生成嘉宾

| 测试名 | 操作 | 预期 |
|--------|------|------|
| `e2e_generate_panel` | POST /panel/generate | 200 + host + N experts |
| `e2e_generate_nonexistent` | 不存在的 discussion_id | 404 |

## E2E-03: 确认阵容

| 测试名 | 操作 | 预期 |
|--------|------|------|
| `e2e_confirm_panel` | PUT /panel 合法阵容 | 200 + panelConfirmed=true |
| `e2e_confirm_twice` | 同一讨论二次确认 | 409 (已确认不可修改) |
| `e2e_confirm_no_host` | 缺少 host 字段 | 422 |

## E2E-04: 状态流转

| 测试名 | 操作 | 预期 |
|--------|------|------|
| `e2e_start_not_confirmed` | 未确认就 start | 409 |
| `e2e_start_ok` | 已确认后 start | 200 + status=live |
| `e2e_pause_resume` | live→pause→live | 状态正确切换 |
| `e2e_end` | live→end | status=ended, 含 endedAt |
| `e2e_cannot_pause_ended` | ended→pause | 409 |
| `e2e_non_creator` | 其他 session 控制 | 403 |

## E2E-05: 报告

| 测试名 | 操作 | 预期 |
|--------|------|------|
| `e2e_report_ended` | GET /report (已结束) | 200 + transcript/consensus/disagreements |
| `e2e_report_live` | GET /report (进行中) | 200 + 空 transcript |

## E2E-06: 错误信息可读性

| 测试名 | 操作 | 预期 |
|--------|------|------|
| `e2e_404_msg` | 不存在的讨论 | {"code":404, "message":"讨论不存在"} |
| `e2e_403_msg` | 非创建者控制 | {"code":403, "message":"非创建者无权操作"} |

## E2E-07: 健康检查

| 测试名 | 操作 | 预期 |
|--------|------|------|
| `e2e_health` | GET /api/health | 200 + status=ok |

## E2E-08: 前端静态检查

| 测试名 | 操作 | 预期 |
|--------|------|------|
| `e2e_frontend_build` | npm run build | 无 TypeScript 错误 |
| `e2e_frontend_tests` | vitest run | 全部通过 |
