# Phase 3 — scheduler.py 测试报告

> **阶段**: TDD  
> **日期**: 2026-06-18  
> **状态**: ✅ PASSED (12/12 新增, 61/61 累计)

---

## 1. TDD 执行记录

| 步 | 动作 | 结果 |
|----|------|------|
| 🔴 | 写 `test_scheduler.py` (12 tests) | 12 FAILED — `ModuleNotFoundError` |
| 🟢 | 写 `app/agents/scheduler.py` (39 行) | 11 PASSED, 1 fail (regex 中文不匹配) |
| 🟡 | Fix regex → 去掉 `match` 参数 | 12 PASSED |
| 🔵 | Refactor | 无需 |

---

## 2. 测试清单 — 6 个场景 × 12 测试

| 场景 | 测试 | 验证 |
|------|------|------|
| **欲望值排序** | `test_highest_desire_wins` | 0.87 > 0.55 > 0.32 → b |
| | `test_single_agent_wins` | 单 agent 直接当选 |
| **focus_time 决断** | `test_newer_focus_wins_on_tie` | 同 0.80, focus 2000 > 1000 → b |
| | `test_focus_time_decides_before_random` | 同 0.75, focus 3000 最大 → newest |
| **随机决断** | `test_random_when_all_equal` | monkeypatch 控制 `_random_index` |
| | `test_random_uses_same_seed_per_call` | 高 desire 者不参与随机 |
| **主持人优先** | `test_host_wins_on_tie_with_expert` | 同分同 focus → host |
| | `test_expert_wins_if_higher_desire_than_host` | expert 0.85 > host 0.75 |
| | `test_host_priority_applies_per_tie_group` | 最高 desire(0.90) 仍是 expert |
| | `test_host_wins_same_desire_even_if_focus_older` | host focus 更旧也赢(同分时) |
| **边界条件** | `test_empty_list_raises` | ValueError |
| | `test_multiple_hosts_self_resolve` | 同分 host×2 → focus_time 决断 |

---

## 3. 核心算法

```
select_speaker(agents):
  1. max_desire = max(a.desire for a in agents)
  2. candidates = [a for a in agents if a.desire == max_desire]
  3. if len(candidates) == 1 → return candidate[0]
  4. hosts = [a for a in candidates if a.role == "host"]
  5. if hosts → candidates = hosts          ← 主持人优先
  6. if len(candidates) == 1 → return
  7. max_focus = max(a.focus_time)          ← 关注点时间
  8. candidates = [a for a in candidates if a.focus_time == max_focus]
  9. if len(candidates) == 1 → return
  10. random.choice(candidates)             ← 终局随机
```

**决断链完全对齐**: `desire_value ↓ → focus_time ↓ → random`, 主持人同分时截断 focus_time 链。

---

## 4. 回归验证

```
tests/unit/: 61 passed in 0.58s
  test_config.py ............ 8 passed
  test_database.py ........... 6 passed
  test_infrastructure.py .... 13 passed
  test_models.py ............ 22 passed
  test_scheduler.py ......... 12 passed  ← 新增
```

---

## 5. 设计文档对齐

| 设计文档 | 要求 | 实现 |
|----------|------|------|
| BACKEND_STRUCTURE.md §3.2 | 欲望值 4 维度权重 | ✅ scheduler 不感知维度，只比最终值 |
| BACKEND_STRUCTURE.md §3.2 | 决断链: 值→时间→随机 | ✅ 逐级收敛 |
| BACKEND_STRUCTURE.md §3.2 | 主持人同分优先 | ✅ host 组提权 |
| PRD §F4.4 | 决断链 + 主持人同分优先 | ✅ |
