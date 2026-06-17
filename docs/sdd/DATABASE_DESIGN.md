# AI Panel Studio — 数据库设计文档

> **阶段**: SDD  
> **日期**: 2026-06-17  
> **数据库**: SQLite  
> **ORM**: SQLAlchemy 2.0 (async)

---

## 1. 实体总览

```
discussions ──┬── panel_members ──┬── utterances
              │                   ├── expert_status_logs
              │                   └── (发言者引用)
              │
              └── consensus_disagreements
```

---

## 2. 表结构详细设计

### 2.1 discussions（讨论主体）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT(36) | PK, UUID4 | 讨论唯一标识 |
| `topic` | TEXT(200) | NOT NULL | 讨论话题 |
| `expert_count` | INTEGER | NOT NULL, DEFAULT 4, CHECK(2-8) | 专家人数 |
| `max_rounds` | INTEGER | NULL | 最大轮次，NULL=不限 |
| `status` | TEXT(10) | NOT NULL, DEFAULT 'pending', CHECK(pending/live/paused/ended) | 讨论状态 |
| `creator_session_id` | TEXT(64) | NOT NULL | 创建者 Session 标识 |
| `current_round` | INTEGER | NOT NULL, DEFAULT 0 | 当前轮次计数 |
| `rounds_without_consensus` | INTEGER | NOT NULL, DEFAULT 0 | 连续无新共识/分歧的轮次 |
| `auto_end_threshold` | INTEGER | NOT NULL, DEFAULT 3 | 连续无共识触发自动结束的阈值 |
| `created_at` | TEXT(25) | NOT NULL, DEFAULT (datetime) | ISO 8601 创建时间 |
| `ended_at` | TEXT(25) | NULL | ISO 8601 结束时间 |

**索引**:
```sql
CREATE INDEX idx_discussions_status ON discussions(status);
CREATE INDEX idx_discussions_created_at ON discussions(created_at DESC);
CREATE INDEX idx_discussions_creator ON discussions(creator_session_id);
```

---

### 2.2 panel_members（嘉宾与主持人）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT(36) | PK, UUID4 | 成员唯一标识 |
| `discussion_id` | TEXT(36) | FK → discussions.id, NOT NULL | 所属讨论 |
| `name` | TEXT(50) | NOT NULL | 姓名 |
| `title` | TEXT(100) | NOT NULL | 职业 / Title |
| `role` | TEXT(6) | NOT NULL, CHECK(host/expert) | 角色 |
| `stance` | TEXT(200) | NOT NULL | 立场描述 |
| `color` | TEXT(7) | NOT NULL, DEFAULT '#3B82F6' | 专属颜色 HEX |
| `avatar_prompt` | TEXT(500) | NULL | 头像生成提示词（v1.1） |
| `sort_order` | INTEGER | NOT NULL, DEFAULT 0 | 排序（主持人=0） |

**索引**:
```sql
CREATE INDEX idx_panel_members_discussion ON panel_members(discussion_id);
CREATE UNIQUE INDEX uq_panel_member_disc_role ON panel_members(discussion_id, role) WHERE role='host';
```

---

### 2.3 utterances（发言记录 / Transcript）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT(36) | PK, UUID4 | 发言唯一标识 |
| `discussion_id` | TEXT(36) | FK → discussions.id, NOT NULL | 所属讨论 |
| `panel_member_id` | TEXT(36) | FK → panel_members.id, NOT NULL | 发言人 |
| `content` | TEXT | NOT NULL | 发言正文 |
| `utterance_type` | TEXT(12) | NOT NULL, CHECK(opening/statement/rebuttal/supplement/question/summary) | 发言类型 |
| `round_num` | INTEGER | NOT NULL | 所属轮次 |
| `sequence_num` | INTEGER | NOT NULL | 全局序号（递增） |
| `is_streaming` | INTEGER | NOT NULL, DEFAULT 0 | 是否正在流式输出（0/1） |
| `created_at` | TEXT(25) | NOT NULL, DEFAULT (datetime) | ISO 8601 创建时间 |

**索引**:
```sql
CREATE INDEX idx_utterances_discussion ON utterances(discussion_id);
CREATE INDEX idx_utterances_member ON utterances(panel_member_id);
CREATE INDEX idx_utterances_sequence ON utterances(discussion_id, sequence_num);
```

---

### 2.4 consensus_disagreements（共识与分歧）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT(36) | PK, UUID4 | 记录唯一标识 |
| `discussion_id` | TEXT(36) | FK → discussions.id, NOT NULL | 所属讨论 |
| `type` | TEXT(13) | NOT NULL, CHECK(consensus/disagreement) | 共识或分歧 |
| `title` | TEXT(200) | NOT NULL | 简短标题 |
| `description` | TEXT(1000) | NOT NULL | 详细说明 |
| `source_utterance_ids` | TEXT | NOT NULL, DEFAULT '[]' | JSON Array: 涉及的发言 ID 列表 |
| `confidence` | REAL | NOT NULL, DEFAULT 1.0, CHECK(0.0-1.0) | 观察员置信度 |
| `is_resolved` | INTEGER | NOT NULL, DEFAULT 0 | 分歧是否已化解（分歧专有） |
| `round_num` | INTEGER | NOT NULL | 产生时的轮次 |
| `created_at` | TEXT(25) | NOT NULL, DEFAULT (datetime) | 创建时间 |
| `updated_at` | TEXT(25) | NOT NULL, DEFAULT (datetime) | 最后更新时间 |

**索引**:
```sql
CREATE INDEX idx_consensus_discussion ON consensus_disagreements(discussion_id);
CREATE INDEX idx_consensus_type ON consensus_disagreements(discussion_id, type);
CREATE INDEX idx_consensus_round ON consensus_disagreements(discussion_id, round_num);
```

---

### 2.5 expert_status_logs（专家状态变更日志）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT(36) | PK, UUID4 | 日志唯一标识 |
| `discussion_id` | TEXT(36) | FK → discussions.id, NOT NULL | 所属讨论 |
| `panel_member_id` | TEXT(36) | FK → panel_members.id, NOT NULL | 专家（仅 role=expert） |
| `status` | TEXT(11) | NOT NULL, CHECK(idle/preparing/speaking) | 状态 |
| `focus_summary` | TEXT(300) | NULL | 公开思考摘要（非 CoT） |
| `desire_value` | REAL | NULL | 当前发言欲望值 |
| `recorded_at` | TEXT(25) | NOT NULL, DEFAULT (datetime) | 记录时间 |

**索引**:
```sql
CREATE INDEX idx_status_log_discussion ON expert_status_logs(discussion_id);
CREATE INDEX idx_status_log_member ON expert_status_logs(panel_member_id);
CREATE INDEX idx_status_log_time ON expert_status_logs(discussion_id, recorded_at DESC);
```

---

## 3. 表关系汇总

| 主表 | 关联表 | 关系 | 外键 |
|------|--------|------|------|
| discussions | panel_members | 1 : N | `panel_members.discussion_id` |
| discussions | utterances | 1 : N | `utterances.discussion_id` |
| discussions | consensus_disagreements | 1 : N | `consensus_disagreements.discussion_id` |
| panel_members | utterances | 1 : N | `utterances.panel_member_id` |
| panel_members | expert_status_logs | 1 : N | `expert_status_logs.panel_member_id` |
| discussions | expert_status_logs | 1 : N | `expert_status_logs.discussion_id` |

---

## 4. 数据库配置

```python
# SQLite WAL 模式 — 支持并发读
DATABASE_URL = "sqlite+aiosqlite:///./data/ai_panel_studio.db"

# 引擎配置
engine_kwargs = {
    "echo": False,
    "connect_args": {
        "check_same_thread": False,  # SQLite 单线程限制解除
    }
}

# 连接时执行 PRAGMA
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()
```

---

## 5. 数据生命周期

```
[创建讨论] → status=pending
     │
     ▼
[生成阵容] → 写入 panel_members
     │
     ▼
[确认阵容] → 不可再编辑 panel_members
     │
     ▼
[开始讨论] → status=live
     │
     ├── [每轮发言] → 写入 utterances + expert_status_logs
     ├── [观察员判断] → 写入/更新 consensus_disagreements
     ├── [暂停] → status=paused
     ├── [继续] → status=live
     │
     ▼
[结束讨论] → status=ended, 记录 ended_at
     │
     ▼
[总结报告] → 最终 utterance (type=summary) + 只读查询汇总
```

---

## 6. 建表 SQL 汇总

完整的 DDL 见附录，此处在 SDD 阶段仅给出关键约束和索引设计。实际建表由 SQLAlchemy 声明式模型自动生成。
