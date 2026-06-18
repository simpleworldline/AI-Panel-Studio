# Phase 6 — discussion_runner.py 测试报告

> **阶段**: TDD  
> **日期**: 2026-06-18  
> **状态**: ✅ PASSED (8/8 新增, 101/101 累计)

---

## 1. TDD 执行记录

| 步 | 动作 | 结果 |
|----|------|------|
| 🔴 | 写 `test_discussion_runner.py` (7 tests) | 7 FAILED — ModuleNotFoundError |
| 🟢 | 写 `discussion_runner.py` (212 行) | 6 PASSED, 1 fail (force_end 竞态 race) |
| 🟡 | Fix 竞态 — 拆分 force_end 为两测, 稳定 race-free | 8 PASSED |
| 🔵 | Refactor | 无需 |

---

## 2. 测试清单 — 6 场景 × 8 测试

| # | 场景 | 测试 | 结果 |
|---|------|------|------|
| 1 | 完整生命周期 | `test_complete_discussion_flow` — 开场→2轮→总结→结束 | ✅ |
| 2 | | `test_opening_utterance_emitted` — 第一条为主持人开场 | ✅ |
| 3 | 结束条件 | `test_max_rounds_triggers_end` — 轮次达上限 | ✅ |
| 4 | | `test_no_consensus_triggers_end` — 连续无共识 | ✅ |
| 5 | 暂停/继续 | `test_pause_stops_loop` — paused 事件 + 循环阻塞 | ✅ |
| 6 | 手动推进 | `test_advance_round_triggers_one_utterance` — 新增发言 | ✅ |
| 7 | 强制结束 | `test_force_end_sets_stop_flag_and_emits_user_ended` | ✅ |
| 8 | | `test_run_stops_on_force_end` — 后台 run 被 force_end 终止 | ✅ |

---

## 3. 核心引擎架构

```
DiscussionRunner.run()
  ├── _start_opening()
  │   ├── host.generate_utterance() → utterance_token ×N → utterance_complete
  │   └── _observer_analyze()
  │
  ├── while not _should_end():
  │   ├── _check_pause()          ← asyncio.Event 阻塞
  │   ├── _run_one_round()
  │   │   ├── scheduler.select_speaker([host, experts])
  │   │   ├── broadcastexpert_status (speaking/idle)
  │   │   ├── winner.generate_utterance() → streaming tokens
  │   │   └── _observer_analyze()
  │   └── current_round++
  │
  ├── _closing()
  │   └── host.generate_utterance(type=summary)
  │
  └── _emit_ended(reason)
```

### 结束条件判断

| 条件 | 触发 |
|------|------|
| `_stop_flag` 被 set | `force_end()` → end_reason="user_ended" |
| `current_round >= max_rounds` | 自动 → end_reason="max_rounds" |
| `rounds_without_consensus >= auto_end_threshold` | 自动 → end_reason="no_consensus" |

### 事件广播覆盖

| WS 事件类型 | 触发位置 |
|------------|----------|
| `expert_status` | 每轮选人后、发言人切换 |
| `utterance_token` | 流式发言逐 token |
| `utterance_complete` | 发言结束 |
| `consensus_update` | 观察员有新判断 |
| `discussion_paused` | `pause()` 调用 |
| `discussion_resumed` | `resume()` 调用 |
| `discussion_ended` | run() 结束 |

---

## 4. 设计文档对齐

| 设计文档 | 要求 | 实现 |
|----------|------|------|
| BACKEND_STRUCTURE.md §3.4 | 调度循环: opening→while→obs→close | ✅ run() |
| BACKEND_STRUCTURE.md §3.4 | 暂停阻塞等待 | ✅ asyncio.Event |
| BACKEND_STRUCTURE.md §3.3 | 观察员每轮分析 | ✅ _observer_analyze() |
| PRD §F8.4 | max_rounds / no_consensus 自动结束 | ✅ _should_end() |
| PRD §F8.1-8.3 | 手动推进 / 暂停 / 强制结束 | ✅ advance_round / pause / force_end |

---

## 5. 回归验证

```
tests/unit/: 101 passed in 5.45s
  test_config.py .............. 8 passed
  test_database.py ............. 6 passed
  test_infrastructure.py ...... 13 passed
  test_models.py .............. 22 passed
  test_scheduler.py ........... 12 passed
  test_llm_client.py .......... 11 passed
  test_expert_agent.py ......... 8 passed
  test_host_agent.py ........... 7 passed
  test_observer_agent.py ....... 6 passed
  test_discussion_runner.py .... 8 passed  ← 新增
```
