"""Discussion 测试数据工厂"""

import uuid
from datetime import datetime, timezone


def make_discussion_row(
    id: str | None = None,
    topic: str = "AI是否应该具备自我意识？",
    expert_count: int = 4,
    max_rounds: int | None = None,
    status: str = "pending",
    creator_session_id: str = "test-session-001",
    current_round: int = 0,
    rounds_without_consensus: int = 0,
    auto_end_threshold: int = 3,
    created_at: str | None = None,
    ended_at: str | None = None,
) -> dict:
    """返回 discussions 表的一行原始数据 (snake_case，模拟 DB 查询)"""
    return {
        "id": id or str(uuid.uuid4()),
        "topic": topic,
        "expert_count": expert_count,
        "max_rounds": max_rounds,
        "status": status,
        "creator_session_id": creator_session_id,
        "current_round": current_round,
        "rounds_without_consensus": rounds_without_consensus,
        "auto_end_threshold": auto_end_threshold,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "ended_at": ended_at,
    }
