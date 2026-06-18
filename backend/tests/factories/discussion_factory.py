"""测试数据工厂 — Discussion"""

import uuid


def make_discussion(
    id: str | None = None,
    topic: str = "测试话题",
    expert_count: int = 4,
    max_rounds: int | None = None,
    status: str = "pending",
    creator_session_id: str = "test-session-001",
    current_round: int = 0,
    **kwargs,
) -> dict:
    return {
        "id": id or str(uuid.uuid4()),
        "topic": topic,
        "expert_count": expert_count,
        "max_rounds": max_rounds,
        "status": status,
        "creator_session_id": creator_session_id,
        "current_round": current_round,
        "created_at": "2026-06-17T10:00:00Z",
        **kwargs,
    }


def make_panel_member(
    id: str | None = None,
    discussion_id: str = "disc-1",
    name: str = "张明",
    title: str = "AI伦理学家",
    role: str = "host",
    stance: str = "中立客观",
    color: str = "#6366F1",
    sort_order: int = 0,
    **kwargs,
) -> dict:
    return {
        "id": id or str(uuid.uuid4()),
        "discussion_id": discussion_id,
        "name": name,
        "title": title,
        "role": role,
        "stance": stance,
        "color": color,
        "sort_order": sort_order,
        **kwargs,
    }
