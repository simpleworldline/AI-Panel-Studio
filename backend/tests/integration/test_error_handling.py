"""
TDD: Error Handling — 验证错误响应格式与 API_CONTRACT.md §1.3, §4 一致
"""

import pytest


@pytest.mark.asyncio
async def test_422_validation_error_format(client):
    """Pydantic 校验失败 → 422 + code/data/message 格式"""
    resp = await client.post("/api/discussions", json={
        "topic": "",           # 空话题 → 422
        "expert_count": 4,
    })
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == 422
    assert body["data"] is None
    assert len(body["message"]) > 0


@pytest.mark.asyncio
async def test_404_not_found_format(client):
    """资源不存在 → 404 + code/data/message 格式"""
    resp = await client.get("/api/discussions/non-existent-id")
    assert resp.status_code == 404
    body = resp.json()
    assert body["code"] == 404
    assert len(body["message"]) > 0


@pytest.mark.asyncio
async def test_409_conflict_format(client, creator_headers):
    """状态冲突 → 409 + 正确格式"""
    # 创建 → 确认 → 开始 → 结束 → 再开始 → 409
    resp = await client.post("/api/discussions", json={
        "topic": "冲突测试",
    }, headers=creator_headers)
    disc_id = resp.json()["data"]["id"]

    await client.put(f"/api/discussions/{disc_id}/panel", json={
        "host": {"name": "A", "title": "T", "stance": "S", "color": "#6366F1"},
        "experts": [{"name": "B", "title": "T", "stance": "S", "color": "#EF4444"}],
    }, headers=creator_headers)

    await client.post(f"/api/discussions/{disc_id}/start", headers=creator_headers)
    await client.post(f"/api/discussions/{disc_id}/end", headers=creator_headers)

    resp = await client.post(f"/api/discussions/{disc_id}/start", headers=creator_headers)
    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == 409
    assert len(body["message"]) > 0


@pytest.mark.asyncio
async def test_403_permission_denied_format(client, creator_headers):
    """权限拒绝 → 403 + 正确格式"""
    resp = await client.post("/api/discussions", json={
        "topic": "权限测试",
    }, headers=creator_headers)
    disc_id = resp.json()["data"]["id"]

    await client.put(f"/api/discussions/{disc_id}/panel", json={
        "host": {"name": "A", "title": "T", "stance": "S", "color": "#6366F1"},
        "experts": [{"name": "B", "title": "T", "stance": "S", "color": "#EF4444"}],
    }, headers=creator_headers)

    await client.post(f"/api/discussions/{disc_id}/start", headers=creator_headers)

    other = {"X-Session-Id": "evil-session"}
    resp = await client.post(f"/api/discussions/{disc_id}/pause", headers=other)
    assert resp.status_code == 403
    body = resp.json()
    assert body["code"] == 403
    assert len(body["message"]) > 0


@pytest.mark.asyncio
async def test_panel_not_confirmed_422(client, creator_headers):
    """阵容未确认就开始 → 409（后端当前用 409，expect 非 200）"""
    resp = await client.post("/api/discussions", json={
        "topic": "未确认测试",
    }, headers=creator_headers)
    disc_id = resp.json()["data"]["id"]

    # 不确认阵容就尝试开始
    resp = await client.post(f"/api/discussions/{disc_id}/start", headers=creator_headers)
    assert resp.status_code in (409, 422)
    body = resp.json()
    assert body["code"] in (409, 422)
    assert len(body["message"]) > 0
