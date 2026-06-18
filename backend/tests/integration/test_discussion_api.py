"""
TDD: Discussion API Integration Tests
依据: API_CONTRACT.md §2.1, §2.3
"""

import uuid
import pytest
from httpx import AsyncClient


@pytest.fixture
def creator_headers():
    return {"X-Session-Id": "test-session-creator"}


# ============================================================
# POST /api/discussions — 创建讨论
# ============================================================
@pytest.mark.asyncio
async def test_create_discussion_success(client: AsyncClient, creator_headers):
    resp = await client.post("/api/discussions", json={
        "topic": "AI是否应该具备自我意识？",
        "expert_count": 6,
        "max_rounds": None,
    }, headers=creator_headers)

    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == 201
    assert body["data"]["topic"] == "AI是否应该具备自我意识？"
    assert body["data"]["expert_count"] == 6
    assert body["data"]["status"] == "pending"
    assert body["data"]["creator_session_id"] == "test-session-creator"
    assert "id" in body["data"]


@pytest.mark.asyncio
async def test_create_discussion_defaults(client: AsyncClient, creator_headers):
    """expert_count 默认 4"""
    resp = await client.post("/api/discussions", json={
        "topic": "默认值测试",
    }, headers=creator_headers)

    assert resp.status_code == 201
    assert resp.json()["data"]["expert_count"] == 4


@pytest.mark.asyncio
async def test_create_discussion_empty_topic(client: AsyncClient, creator_headers):
    resp = await client.post("/api/discussions", json={
        "topic": "",
    }, headers=creator_headers)

    assert resp.status_code == 422
    assert resp.json()["code"] == 422


@pytest.mark.asyncio
async def test_create_discussion_topic_too_long(client: AsyncClient, creator_headers):
    resp = await client.post("/api/discussions", json={
        "topic": "A" * 201,
    }, headers=creator_headers)

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_discussion_expert_count_too_low(client: AsyncClient, creator_headers):
    resp = await client.post("/api/discussions", json={
        "topic": "测试",
        "expert_count": 1,
    }, headers=creator_headers)

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_discussion_expert_count_too_high(client: AsyncClient, creator_headers):
    resp = await client.post("/api/discussions", json={
        "topic": "测试",
        "expert_count": 9,
    }, headers=creator_headers)

    assert resp.status_code == 422


# ============================================================
# GET /api/discussions — 讨论列表
# ============================================================
@pytest.mark.asyncio
async def test_list_discussions_empty(client: AsyncClient):
    resp = await client.get("/api/discussions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["items"] == []
    assert body["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_discussions_with_data(client: AsyncClient, creator_headers):
    # 先创建一条
    await client.post("/api/discussions", json={"topic": "测试1"}, headers=creator_headers)
    await client.post("/api/discussions", json={"topic": "测试2"}, headers=creator_headers)

    resp = await client.get("/api/discussions")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["total"] >= 2
    assert len(body["data"]["items"]) >= 2


@pytest.mark.asyncio
async def test_list_discussions_filter_by_status(client: AsyncClient, creator_headers):
    await client.post("/api/discussions", json={"topic": "待开始"}, headers=creator_headers)
    resp = await client.get("/api/discussions?status=pending")
    assert resp.status_code == 200
    for item in resp.json()["data"]["items"]:
        assert item["status"] == "pending"


@pytest.mark.asyncio
async def test_list_discussions_paginated(client: AsyncClient, creator_headers):
    resp = await client.get("/api/discussions?page=1&page_size=5")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["page"] == 1
    assert body["data"]["page_size"] == 5


# ============================================================
# GET /api/discussions/{id} — 讨论详情
# ============================================================
@pytest.mark.asyncio
async def test_get_discussion_detail(client: AsyncClient, creator_headers):
    create_resp = await client.post("/api/discussions", json={
        "topic": "详情测试",
        "expert_count": 4,
    }, headers=creator_headers)
    disc_id = create_resp.json()["data"]["id"]

    resp = await client.get(f"/api/discussions/{disc_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["topic"] == "详情测试"
    assert body["data"]["expert_count"] == 4
    assert "panel" in body["data"]
    assert "transcript" in body["data"]
    assert "consensus" in body["data"]
    assert "disagreements" in body["data"]


@pytest.mark.asyncio
async def test_get_discussion_not_found(client: AsyncClient):
    resp = await client.get("/api/discussions/non-existent-id")
    assert resp.status_code == 404


# ============================================================
# 讨论控制 — POST start/pause/resume/next/end
# ============================================================
@pytest.mark.asyncio
async def test_start_discussion(client: AsyncClient, creator_headers):
    # 创建 + 确认阵容
    create_resp = await client.post("/api/discussions", json={
        "topic": "启动测试",
    }, headers=creator_headers)
    disc_id = create_resp.json()["data"]["id"]
    await client.put(f"/api/discussions/{disc_id}/panel", json={
        "host": {"name": "张明", "title": "T", "stance": "S", "color": "#6366F1"},
        "experts": [
            {"name": "李研究员", "title": "T", "stance": "S", "color": "#EF4444"},
        ],
    }, headers=creator_headers)

    resp = await client.post(f"/api/discussions/{disc_id}/start", headers=creator_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "live"


@pytest.mark.asyncio
async def test_pause_resume_discussion(client: AsyncClient, creator_headers):
    create_resp = await client.post("/api/discussions", json={
        "topic": "暂停测试",
    }, headers=creator_headers)
    disc_id = create_resp.json()["data"]["id"]
    await client.put(f"/api/discussions/{disc_id}/panel", json={
        "host": {"name": "张明", "title": "T", "stance": "S", "color": "#6366F1"},
        "experts": [{"name": "李", "title": "T", "stance": "S", "color": "#EF4444"}],
    }, headers=creator_headers)
    await client.post(f"/api/discussions/{disc_id}/start", headers=creator_headers)

    pause_resp = await client.post(f"/api/discussions/{disc_id}/pause", headers=creator_headers)
    assert pause_resp.json()["data"]["status"] == "paused"

    resume_resp = await client.post(f"/api/discussions/{disc_id}/resume", headers=creator_headers)
    assert resume_resp.json()["data"]["status"] == "live"


@pytest.mark.asyncio
async def test_end_discussion(client: AsyncClient, creator_headers):
    create_resp = await client.post("/api/discussions", json={
        "topic": "结束测试",
    }, headers=creator_headers)
    disc_id = create_resp.json()["data"]["id"]
    await client.put(f"/api/discussions/{disc_id}/panel", json={
        "host": {"name": "张明", "title": "T", "stance": "S", "color": "#6366F1"},
        "experts": [{"name": "李", "title": "T", "stance": "S", "color": "#EF4444"}],
    }, headers=creator_headers)
    await client.post(f"/api/discussions/{disc_id}/start", headers=creator_headers)

    resp = await client.post(f"/api/discussions/{disc_id}/end", headers=creator_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ended"


@pytest.mark.asyncio
async def test_next_round_advance(client: AsyncClient, creator_headers):
    create_resp = await client.post("/api/discussions", json={
        "topic": "推进测试",
    }, headers=creator_headers)
    disc_id = create_resp.json()["data"]["id"]
    await client.put(f"/api/discussions/{disc_id}/panel", json={
        "host": {"name": "张明", "title": "T", "stance": "S", "color": "#6366F1"},
        "experts": [{"name": "李", "title": "T", "stance": "S", "color": "#EF4444"}],
    }, headers=creator_headers)
    await client.post(f"/api/discussions/{disc_id}/start", headers=creator_headers)

    resp = await client.post(f"/api/discussions/{disc_id}/next", headers=creator_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["round_triggered"] is True


# ============================================================
# 权限校验
# ============================================================
@pytest.mark.asyncio
async def test_non_creator_cannot_control(client: AsyncClient, creator_headers):
    create_resp = await client.post("/api/discussions", json={
        "topic": "权限测试",
    }, headers=creator_headers)
    disc_id = create_resp.json()["data"]["id"]
    await client.put(f"/api/discussions/{disc_id}/panel", json={
        "host": {"name": "张明", "title": "T", "stance": "S", "color": "#6366F1"},
        "experts": [{"name": "李", "title": "T", "stance": "S", "color": "#EF4444"}],
    }, headers=creator_headers)
    await client.post(f"/api/discussions/{disc_id}/start", headers=creator_headers)

    # 另一个 Session 尝试控制
    other_headers = {"X-Session-Id": "non-creator-session"}
    resp = await client.post(f"/api/discussions/{disc_id}/pause", headers=other_headers)
    assert resp.status_code == 403


# ============================================================
# 状态冲突
# ============================================================
@pytest.mark.asyncio
async def test_cannot_start_ended_discussion(client: AsyncClient, creator_headers):
    create_resp = await client.post("/api/discussions", json={
        "topic": "冲突测试",
    }, headers=creator_headers)
    disc_id = create_resp.json()["data"]["id"]
    await client.put(f"/api/discussions/{disc_id}/panel", json={
        "host": {"name": "张明", "title": "T", "stance": "S", "color": "#6366F1"},
        "experts": [{"name": "李", "title": "T", "stance": "S", "color": "#EF4444"}],
    }, headers=creator_headers)
    await client.post(f"/api/discussions/{disc_id}/start", headers=creator_headers)
    await client.post(f"/api/discussions/{disc_id}/end", headers=creator_headers)

    resp = await client.post(f"/api/discussions/{disc_id}/start", headers=creator_headers)
    assert resp.status_code == 409


# ============================================================
# GET /api/discussions/{id}/report
# ============================================================
@pytest.mark.asyncio
async def test_get_report(client: AsyncClient, creator_headers):
    create_resp = await client.post("/api/discussions", json={
        "topic": "报告测试",
    }, headers=creator_headers)
    disc_id = create_resp.json()["data"]["id"]
    await client.put(f"/api/discussions/{disc_id}/panel", json={
        "host": {"name": "张明", "title": "T", "stance": "S", "color": "#6366F1"},
        "experts": [{"name": "李", "title": "T", "stance": "S", "color": "#EF4444"}],
    }, headers=creator_headers)
    await client.post(f"/api/discussions/{disc_id}/start", headers=creator_headers)
    await client.post(f"/api/discussions/{disc_id}/end", headers=creator_headers)

    resp = await client.get(f"/api/discussions/{disc_id}/report")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["discussion_id"] == disc_id
    assert "transcript" in body["data"]
    assert "consensus" in body["data"]
    assert "disagreements" in body["data"]
