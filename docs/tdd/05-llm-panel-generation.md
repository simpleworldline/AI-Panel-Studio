# TDD: LLM 嘉宾生成

> **日期**: 2026-06-18  
> **被测模块**: `app/services/panel_service.py` → `generate_panel()`  
> **依据**: PRD §2.2 F2.3, TECH_STACK.md §3.3

---

## 当前问题

`generate_panel()` 返回硬编码 mock 数据，未调用 DeepSeek API。

## 修复方案

1. 构建 LLM prompt：根据话题 + 专家人数，生成 1 位主持人 + N 位专家
2. 调用 `llm_client.chat()` → 返回 JSON
3. 解析 JSON → 分配颜色 → 返回结构化数据
4. JSON 解析失败时 fallback 到 mock

## 测试用例

| 测试名 | 验证点 |
|--------|--------|
| `test_generate_calls_llm` | generate_panel 调用 LLM 而非返回硬编码 |
| `test_generate_prompt_format` | prompt 包含话题 + 人数 + JSON 格式要求 |
| `test_generate_parse_valid_json` | 合法 JSON 正确解析 |
| `test_generate_fallback_on_parse_error` | JSON 非法时 fallback mock |
| `test_generate_returns_correct_count` | experts 数量 = expert_count |
