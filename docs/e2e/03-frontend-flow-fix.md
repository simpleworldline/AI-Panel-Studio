# E2E-03: 前端页面流转修复

> **日期**: 2026-06-18  
> **问题**: 首页不显示讨论 + 确认嘉宾后无法进入演播厅

---

## 根因分析

### Bug 1: 首页不显示已创建的讨论
- **根因**: HomePage 仅查询 `status=live` 和 `status=ended`，但新创建的讨论 status=`pending`
- **影响**: 创建讨论并确认嘉宾后，讨论仍为 pending，不会出现在首页任何 Tab
- **修复**: HomePage 增加"待开始"Tab 或在确认嘉宾后自动调用 start

### Bug 2: 确认嘉宾后无法进入讨论
- **根因**: PanelSetupPage → StudioPage 跳转后，讨论 status 仍为 `pending`，StudioPage 没有"开始讨论"入口
- **影响**: 用户看到演播厅 UI 但无法推进讨论
- **修复**: StudioPage 增加"开始讨论"按钮，当 isCreator && status==='pending' 时显示

### Bug 3: 后端 get_detail 存在潜在 MissingGreenlet
- **根因**: `selectinload(Discussion.utterances)` 加载了 utterances 但未加载 `Utterance.panel_member` 关系，生产环境访问 `u.panel_member.name` 可能触发 lazy load 失败
- **修复**: 使用链式 selectinload 或改用 join 查询

---

## 测试用例

| 测试名 | 操作 | 预期 |
|--------|------|------|
| `e2e_home_shows_pending` | 创建+确认后回到首页 | 讨论出现在列表中 |
| `e2e_studio_can_start` | 确认后进入演播厅 | 显示"开始讨论"按钮 |
| `e2e_studio_start_works` | 点击开始 → 讨论进行 | status 变为 live，显示控制栏 |
| `e2e_detail_no_lazy_load_error` | 获取详情 | 无 MissingGreenlet 错误 |
