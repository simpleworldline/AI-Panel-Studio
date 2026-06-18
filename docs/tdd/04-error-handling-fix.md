# 错误处理修复 — TDD 测试文档

> **阶段**: TDD — Bug Fix
> **日期**: 2026-06-18
> **问题**: 用户确认嘉宾阵容时显示 "网络错误，请稍后重试"，无法看到真实错误原因
> **根因**: FastAPI HTTPException 返回 `{"detail":"..."}` 格式，前端拦截器只取 `data?.message`

---

## 测试用例

### 后端测试
| 测试名 | 验证点 | 预期 |
|--------|--------|------|
| `test_404_error_format` | 404 响应包含 code/data/message | HTTP 404 + body.code=404 |
| `test_403_error_format` | 403 响应格式统一 | HTTP 403 + body.message 非空 |
| `test_409_error_format` | 409 响应格式统一 | body.code=409 + message=原始错误 |
| `test_422_error_format` | 422 验证失败格式 | body.code=422 + message 说明原因 |

### 前端测试
| 测试名 | 验证点 |
|--------|--------|
| `test_error_handler_detail` | 后端返回 `{"detail":"msg"}` → 前端正确提取 `"msg"` |
| `test_error_handler_message` | 后端返回 `{"code":409,"message":"msg"}` → 优先使用 message |
