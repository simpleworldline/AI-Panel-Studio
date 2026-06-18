# Phase 2 — SQLAlchemy 模型测试报告

> **阶段**: TDD  
> **日期**: 2026-06-18  
> **状态**: ✅ PASSED (22/22 新增, 49/49 累计)

---

## 1. TDD 执行记录

| 步 | 动作 | 结果 |
|----|------|------|
| 🔴 | 写 `test_models.py` (22 tests) | 22 ERROR — ModuleNotFoundError |
| 🟢 | 写 5 个 model 文件 + `app/models/__init__.py` | 21 PASSED, 1 FK fail |
| 🟡 | 修复所有 FK 依赖 (测试补父行) | 22 PASSED |
| 🔵 | Refactor | 无需 — 每表 20-30 行刚好 |

---

## 2. 测试清单

| # | 模型 | 测试 | 验证内容 |
|---|------|------|----------|
| 1 | Discussion | `test_table_exists` | 表成功创建 |
| 2 | | `test_insert_and_query` | 写入+读取 |
| 3 | | `test_default_values` | expert_count=4, status=pending 5个默认值 |
| 4 | | `test_max_rounds_nullable` | NULL 值写入 |
| 5 | | `test_status_constraint` | pending/live/paused/ended 四种 |
| 6 | PanelMember | `test_insert_host` | 主持人插入 (role=host, sort_order=0) |
| 7 | | `test_insert_expert` | 专家插入 |
| 8 | | `test_color_default` | color 默认值 #3B82F6 |
| 9 | | `test_avatar_prompt_nullable` | NULL 字段 |
| 10 | | `test_role_constraint` | host/expert 两种角色 |
| 11 | Utterance | `test_insert_utterance` | 发言写入 |
| 12 | | `test_is_streaming_default_zero` | 默认值为 0 |
| 13 | | `test_utterance_type_constraint` | 6 种类型全部合法 |
| 14 | Consensus | `test_insert_consensus` | 共识写入 |
| 15 | | `test_insert_disagreement` | 分歧写入 |
| 16 | | `test_default_values` | confidence=1.0, is_resolved=0, source_ids='[]' |
| 17 | | `test_type_constraint` | consensus/disagreement |
| 18 | | `test_confidence_range` | 0.0 / 0.5 / 1.0 均合法 |
| 19 | ExpertStatusLog | `test_insert_status_log` | 状态日志写入 |
| 20 | | `test_focus_summary_nullable` | NULL 字段 |
| 21 | | `test_status_constraint` | idle/preparing/speaking 三种 |
| 22 | All | `test_five_tables_exist` | 5 张表全部创建 |

---

## 3. 新增生产代码

| 文件 | 模型 | 对齐 |
|------|------|------|
| `app/models/__init__.py` | `Base` (DeclarativeBase) | — |
| `app/models/discussion.py` | `Discussion` | DATABASE_DESIGN.md §2.1 |
| `app/models/panel_member.py` | `PanelMember` | DATABASE_DESIGN.md §2.2 |
| `app/models/utterance.py` | `Utterance` | DATABASE_DESIGN.md §2.3 |
| `app/models/consensus.py` | `ConsensusDisagreement` | DATABASE_DESIGN.md §2.4 |
| `app/models/expert_status_log.py` | `ExpertStatusLog` | DATABASE_DESIGN.md §2.5 |

全部使用 SQLAlchemy 2.0 `Mapped[]` + `mapped_column()` 声明式映射，与 BACKEND_STRUCTURE.md §5 一致。

---

## 4. 回归验证

```
tests/unit/: 49 passed in 0.56s
  test_config.py ........... 8 passed
  test_database.py .......... 6 passed
  test_infrastructure.py ... 13 passed
  test_models.py ........... 22 passed
```

零回归，零生产代码修改。

---

## 5. 约束/默认值/索引覆盖

| 数据库设计 | 实现 |
|------------|------|
| Discussion.status CHECK 4 值 | ✅ `ck_discussions_status` |
| Discussion.expert_count CHECK 2-8 | ✅ `ck_discussions_expert_count` |
| Discussion.expert_count DEFAULT 4 | ✅ |
| Discussion.auto_end_threshold DEFAULT 3 | ✅ |
| PanelMember.role CHECK host/expert | ✅ `ck_panel_members_role` |
| PanelMember.color DEFAULT #3B82F6 | ✅ |
| Utterance.utterance_type CHECK 6 值 | ✅ `ck_utterances_type` |
| Utterance.is_streaming DEFAULT 0 | ✅ |
| Consensus.type CHECK consensus/disagreement | ✅ `ck_consensus_type` |
| Consensus.confidence CHECK 0.0-1.0 | ✅ `ck_consensus_confidence` |
| Consensus.confidence DEFAULT 1.0 | ✅ |
| Consensus.is_resolved DEFAULT 0 | ✅ |
| Consensus.source_utterance_ids DEFAULT '[]' | ✅ |
| ExpertStatusLog.status CHECK 3 值 | ✅ `ck_expert_status_logs_status` |
