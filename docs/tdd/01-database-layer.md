# 数据库层测试文档 (TDD: Database Layer)

> **阶段**: TDD — RED  
> **日期**: 2026-06-18  
> **被测模块**: `app/models/` + `app/db/`  
> **依据文档**: DATABASE_DESIGN.md, ER_DIAGRAM.md, TECH_STACK.md

---

## 1. 测试范围

| 被测对象 | 文件 | 设计文档依据 |
|----------|------|-------------|
| 数据库引擎创建 | `app/db/database.py` | TECH_STACK.md §3.2, DATABASE_DESIGN.md §4 |
| 会话工厂 + 依赖注入 | `app/db/session.py` | BACKEND_STRUCTURE.md §2.4 |
| Discussion 模型 | `app/models/discussion.py` | DATABASE_DESIGN.md §2.1 |
| PanelMember 模型 | `app/models/panel_member.py` | DATABASE_DESIGN.md §2.2 |
| Utterance 模型 | `app/models/utterance.py` | DATABASE_DESIGN.md §2.3 |
| ConsensusDisagreement 模型 | `app/models/consensus.py` | DATABASE_DESIGN.md §2.4 |
| ExpertStatusLog 模型 | `app/models/expert_status_log.py` | DATABASE_DESIGN.md §2.5 |

---

## 2. 测试用例

### 2.1 表存在性验证

| 测试名 | 验证点 | 预期结果 |
|--------|--------|----------|
| `test_tables_exist` | 5张表全部创建 | `discussions`, `panel_members`, `utterances`, `consensus_disagreements`, `expert_status_logs` 都存在 |

### 2.2 表结构验证（按 DATABASE_DESIGN.md §2）

| 测试名 | 表 | 验证点 |
|--------|-----|--------|
| `test_discussions_columns` | discussions | 11个字段名+类型+nullable+PK 均与 §2.1 一致 |
| `test_panel_members_columns` | panel_members | 9个字段 + FK + 索引 |
| `test_utterances_columns` | utterances | 9个字段 + FK 关联 discussions 和 panel_members |
| `test_consensus_disagreements_columns` | consensus_disagreements | 11个字段 |
| `test_expert_status_logs_columns` | expert_status_logs | 7个字段 |

### 2.3 业务约束验证

| 测试名 | 验证点 | 预期 |
|--------|--------|------|
| `test_discussion_status_check` | status 只能是 pending/live/paused/ended | 非法 status 抛出 IntegrityError |
| `test_expert_count_check` | expert_count 必须在 2-8 | 越界值抛出 IntegrityError |
| `test_unique_host_per_discussion` | (discussion_id, role='host') 唯一 | 第二个 host 抛 IntegrityError |
| `test_expert_status_check` | status 只能是 idle/preparing/speaking | 非法值抛 IntegrityError |
| `test_utterance_type_check` | utterance_type 6种取值 | 非法值抛 IntegrityError |
| `test_consensus_type_check` | type 只能是 consensus/disagreement | 非法值抛 IntegrityError |

### 2.4 CRUD 与关系验证

| 测试名 | 验证点 |
|--------|--------|
| `test_discussion_crud` | Discussion 完整 CRUD 流程 |
| `test_panel_member_relationship` | Discussion 1:N PanelMember，通过 select 查询避免 greenlet 问题 |
| `test_panel_member_relationship_eager` | Discussion 1:N — selectinload eager loading 方式 |
| `test_utterance_relationship` | Utterance 关联 Discussion 和 PanelMember |
| `test_consensus_relationship` | ConsensusDisagreement 关联 Discussion |
| `test_expert_status_log_relationship` | ExpertStatusLog 关联 Discussion 和 PanelMember |
| `test_cascade_delete` | 删除 Discussion 时级联删除所有关联数据 |

### 2.5 默认值与自动生成

| 测试名 | 验证点 |
|--------|--------|
| `test_discussion_defaults` | expert_count 默认4, status 默认'pending', current_round 默认0, rounds_without_consensus 默认0 |
| `test_utterance_defaults` | is_streaming 默认0, sequence_num 自动递增 |

### 2.6 数据库配置验证

| 测试名 | 验证点 |
|--------|--------|
| `test_engine_creation` | async engine 创建成功，WAL 模式启用 |
| `test_session_factory` | sessionmaker 工厂可用 |

---

## 3. 测试策略

- 使用 **SQLite in-memory** 数据库（`sqlite+aiosqlite://`），每次测试独立建表/删表
- 所有 fixture 在 `conftest.py` 中定义
- 遵循 RED → 确认失败原因 → GREEN → REFACTOR 循环

---

## 4. 预期失败原因（RED 阶段）

当前 `app/models/` 和 `app/db/` 目录为空，所有测试应该因为 **ImportError** 或 **表不存在** 而失败。
