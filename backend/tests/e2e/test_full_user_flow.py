"""
E2E: Full User Flow — 模拟用户从创建到报告的完整流程
依据: docs/e2e/01-full-user-flow.md
"""

import uuid
import pytest
from httpx import AsyncClient


@pytest.fixture
def session_a():
    return {"X-Session-Id": f"user-a-{uuid.uuid4().hex[:8]}"}

@pytest.fixture
def session_b():
    return {"X-Session-Id": f"user-b-{uuid.uuid4().hex[:8]}"}


# ═══════════════════════════════════════════════════════════
# E2E-01: 创建讨论
# ═══════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_e2e_create_valid(client: AsyncClient, session_a):
    resp = await client.post("/api/discussions", json={
        "topic": "AI是否应该具备自我意识？", "expert_count": 6, "max_rounds": None,
    }, headers=session_a)
    assert resp.status_code == 201
    body = resp.json()
    assert body["code"] == 201
    d = body["data"]
    assert d["topic"] == "AI是否应该具备自我意识？"
    assert d["expert_count"] == 6
    assert d["status"] == "pending"
    assert d["current_round"] == 0
    assert "id" in d
    assert "created_at" in d


@pytest.mark.asyncio
async def test_e2e_create_defaults(client: AsyncClient, session_a):
    resp = await client.post("/api/discussions", json={"topic": "默认值测试"}, headers=session_a)
    assert resp.status_code == 201
    d = resp.json()["data"]
    assert d["expert_count"] == 4
    assert d["status"] == "pending"


@pytest.mark.asyncio
async def test_e2e_create_empty_topic(client: AsyncClient, session_a):
    resp = await client.post("/api/discussions", json={"topic": ""}, headers=session_a)
    assert resp.status_code == 422
    assert resp.json()["code"] == 422


@pytest.mark.asyncio
async def test_e2e_create_topic_200_chars(client: AsyncClient, session_a):
    resp = await client.post("/api/discussions", json={"topic": "A" * 200}, headers=session_a)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_e2e_create_topic_201_chars(client: AsyncClient, session_a):
    resp = await client.post("/api/discussions", json={"topic": "A" * 201}, headers=session_a)
    assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════
# E2E-02: 生成嘉宾阵容
# ═══════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_e2e_generate_panel(client: AsyncClient, session_a):
    # 1. 创建讨论
    resp = await client.post("/api/discussions", json={"topic": "嘉宾测试", "expert_count": 6}, headers=session_a)
    disc_id = resp.json()["data"]["id"]

    # 2. 生成嘉宾
    resp = await client.post(f"/api/discussions/{disc_id}/panel/generate")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["host"] is not None
    host = body["data"]["host"]
    assert len(host["name"]) > 0
    assert len(host["title"]) > 0
    assert host["color"].startswith("#")

    experts = body["data"]["experts"]
    assert len(experts) == 6  # match expert_count
    for e in experts:
        assert len(e["name"]) > 0
        assert e["color"].startswith("#")


@pytest.mark.asyncio
async def test_e2e_generate_nonexistent(client: AsyncClient):
    resp = await client.post("/api/discussions/fake-id-123/panel/generate")
    assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════
# E2E-03: 确认阵容
# ═══════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_e2e_confirm_panel(client: AsyncClient, session_a):
    resp = await client.post("/api/discussions", json={"topic": "确认测试"}, headers=session_a)
    disc_id = resp.json()["data"]["id"]

    resp = await client.put(f"/api/discussions/{disc_id}/panel", json={
        "host": {"name": "张明", "title": "AI伦理学家", "stance": "中立", "color": "#6366F1"},
        "experts": [
            {"name": "李研究员", "title": "认知科学", "stance": "支持", "color": "#EF4444"},
            {"name": "王教授", "title": "计算机科学", "stance": "反对", "color": "#10B981"},
            {"name": "陈博士", "title": "神经科学", "stance": "中立", "color": "#F59E0B"},
        ],
    }, headers=session_a)
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["panel_confirmed"] is True
    assert body["data"]["discussion_id"] == disc_id
    assert len(body["data"]["members"]) == 4  # 1 host + 3 experts


@pytest.mark.asyncio
async def test_e2e_confirm_twice_409(client: AsyncClient, session_a):
    resp = await client.post("/api/discussions", json={"topic": "二次确认"}, headers=session_a)
    disc_id = resp.json()["data"]["id"]

    payload = {
        "host": {"name": "A", "title": "T", "stance": "S", "color": "#6366F1"},
        "experts": [{"name": "B", "title": "T", "stance": "S", "color": "#EF4444"}],
    }
    r1 = await client.put(f"/api/discussions/{disc_id}/panel", json=payload, headers=session_a)
    assert r1.status_code == 200

    r2 = await client.put(f"/api/discussions/{disc_id}/panel", json=payload, headers=session_a)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_e2e_confirm_no_host_422(client: AsyncClient, session_a):
    resp = await client.post("/api/discussions", json={"topic": "缺主持"}, headers=session_a)
    disc_id = resp.json()["data"]["id"]

    # 发送不完整 JSON — host 为空对象会被 Pydantic 拒绝
    resp = await client.put(f"/api/discussions/{disc_id}/panel", json={
        "experts": [{"name": "B", "title": "T", "stance": "S", "color": "#EF4444"}],
    }, headers=session_a)
    assert resp.status_code in (422, 400)


# ═══════════════════════════════════════════════════════════
# E2E-04: 讨论状态流转
# ═══════════════════════════════════════════════════════════
async def _setup_discussion_live(client, session):
    """Helper: 创建讨论 → 确认阵容 → 开始 → 返回 disc_id"""
    r = await client.post("/api/discussions", json={"topic": "状态测试"}, headers=session)
    disc_id = r.json()["data"]["id"]
    await client.put(f"/api/discussions/{disc_id}/panel", json={
        "host": {"name": "A", "title": "T", "stance": "S", "color": "#6366F1"},
        "experts": [{"name": "B", "title": "T", "stance": "S", "color": "#EF4444"}],
    }, headers=session)
    await client.post(f"/api/discussions/{disc_id}/start", headers=session)
    return disc_id


@pytest.mark.asyncio
async def test_e2e_start_not_confirmed_409(client: AsyncClient, session_a):
    r = await client.post("/api/discussions", json={"topic": "未确认开始"}, headers=session_a)
    disc_id = r.json()["data"]["id"]
    r = await client.post(f"/api/discussions/{disc_id}/start", headers=session_a)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_e2e_start_ok(client: AsyncClient, session_a):
    r = await client.post("/api/discussions", json={"topic": "合法开始"}, headers=session_a)
    disc_id = r.json()["data"]["id"]
    await client.put(f"/api/discussions/{disc_id}/panel", json={
        "host": {"name": "A", "title": "T", "stance": "S", "color": "#6366F1"},
        "experts": [{"name": "B", "title": "T", "stance": "S", "color": "#EF4444"}],
    }, headers=session_a)
    r = await client.post(f"/api/discussions/{disc_id}/start", headers=session_a)
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "live"


@pytest.mark.asyncio
async def test_e2e_pause_resume(client: AsyncClient, session_a):
    disc_id = await _setup_discussion_live(client, session_a)

    r = await client.post(f"/api/discussions/{disc_id}/pause", headers=session_a)
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "paused"

    r = await client.post(f"/api/discussions/{disc_id}/resume", headers=session_a)
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "live"


@pytest.mark.asyncio
async def test_e2e_end(client: AsyncClient, session_a):
    disc_id = await _setup_discussion_live(client, session_a)

    r = await client.post(f"/api/discussions/{disc_id}/end", headers=session_a)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["status"] == "ended"
    assert d["ended_at"] is not None
    assert "total_rounds" in d
    assert "total_utterances" in d


@pytest.mark.asyncio
async def test_e2e_next_round(client: AsyncClient, session_a):
    disc_id = await _setup_discussion_live(client, session_a)

    r = await client.post(f"/api/discussions/{disc_id}/next", headers=session_a)
    assert r.status_code == 200
    assert r.json()["data"]["round_triggered"] is True


@pytest.mark.asyncio
async def test_e2e_cannot_pause_ended_409(client: AsyncClient, session_a):
    disc_id = await _setup_discussion_live(client, session_a)
    await client.post(f"/api/discussions/{disc_id}/end", headers=session_a)

    r = await client.post(f"/api/discussions/{disc_id}/pause", headers=session_a)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_e2e_non_creator_403(client: AsyncClient, session_a, session_b):
    disc_id = await _setup_discussion_live(client, session_a)

    r = await client.post(f"/api/discussions/{disc_id}/pause", headers=session_b)
    assert r.status_code == 403
    assert r.json()["code"] == 403
    assert len(r.json()["message"]) > 0


# ═══════════════════════════════════════════════════════════
# E2E-05: 报告
# ═══════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_e2e_report_ended(client: AsyncClient, session_a):
    disc_id = await _setup_discussion_live(client, session_a)
    await client.post(f"/api/discussions/{disc_id}/end", headers=session_a)

    r = await client.get(f"/api/discussions/{disc_id}/report")
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["discussion_id"] == disc_id
    assert "topic" in d
    assert "panel" in d
    assert "transcript" in d
    assert "consensus" in d
    assert "disagreements" in d
    assert "host_summary" in d


@pytest.mark.asyncio
async def test_e2e_report_live(client: AsyncClient, session_a):
    disc_id = await _setup_discussion_live(client, session_a)

    r = await client.get(f"/api/discussions/{disc_id}/report")
    assert r.status_code == 200
    assert "transcript" in r.json()["data"]


# ═══════════════════════════════════════════════════════════
# E2E-06: 错误信息可读性
# ═══════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_e2e_404_msg_chinese(client: AsyncClient):
    r = await client.get("/api/discussions/non-existent")
    assert r.status_code == 404
    b = r.json()
    assert b["code"] == 404
    assert b["data"] is None
    assert "讨论" in b["message"]  # 中文错误信息


@pytest.mark.asyncio
async def test_e2e_403_msg_chinese(client: AsyncClient, session_a, session_b):
    disc_id = await _setup_discussion_live(client, session_a)

    # 直接用 session_b 调取任务
    r = await client.post(f"/api/discussions/{disc_id}/pause", headers=session_b)
    assert r.status_code == 403
    assert "非创建者" in r.json()["message"] or "无权" in r.json()["message"]


# ═══════════════════════════════════════════════════════════
# E2E-07: 健康检查
# ═══════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_e2e_health(client: AsyncClient):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "ok"


# ═══════════════════════════════════════════════════════════
# E2E-08: 列表 + 详情聚合
# ═══════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_e2e_list_filtered_by_status(client: AsyncClient, session_a):
    # 创建几条并让一条变成 live
    for i in range(3):
        r = await client.post("/api/discussions", json={"topic": f"列表测试{i}"}, headers=session_a)
        disc_id = r.json()["data"]["id"]
        await client.put(f"/api/discussions/{disc_id}/panel", json={
            "host": {"name": "X", "title": "T", "stance": "S", "color": "#6366F1"},
            "experts": [{"name": "Y", "title": "T", "stance": "S", "color": "#EF4444"}],
        }, headers=session_a)
        if i == 0:
            await client.post(f"/api/discussions/{disc_id}/start", headers=session_a)

    r = await client.get("/api/discussions?status=live")
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    for item in items:
        assert item["status"] == "live"

    r2 = await client.get("/api/discussions?status=pending")
    pending_items = r2.json()["data"]["items"]
    for item in pending_items:
        assert item["status"] == "pending"


@pytest.mark.asyncio
async def test_e2e_detail_has_panel_and_transcript(client: AsyncClient, session_a):
    r = await client.post("/api/discussions", json={"topic": "详情聚合"}, headers=session_a)
    disc_id = r.json()["data"]["id"]
    await client.put(f"/api/discussions/{disc_id}/panel", json={
        "host": {"name": "张明", "title": "AI伦理学家", "stance": "中立", "color": "#6366F1"},
        "experts": [
            {"name": "李研究员", "title": "认知科学", "stance": "支持", "color": "#EF4444"},
        ],
    }, headers=session_a)

    r = await client.get(f"/api/discussions/{disc_id}")
    assert r.status_code == 200
    d = r.json()["data"]
    assert len(d["panel"]) == 2
    assert d["panel"][0]["role"] == "host"
    assert d["transcript"] == []
    assert d["consensus"] == []
    assert d["disagreements"] == []


# ═══════════════════════════════════════════════════════════
# E2E-09: 完整串联流程
# ═══════════════════════════════════════════════════════════
@pytest.mark.asyncio
async def test_e2e_full_lifecycle(client: AsyncClient, session_a):
    """完整端到端：创建 → 生成 → 确认 → 开始 → 暂停 → 继续 → 结束 → 报告"""
    # 1. 创建
    r = await client.post("/api/discussions", json={
        "topic": "人类是否应该追求永生？", "expert_count": 3,
    }, headers=session_a)
    assert r.status_code == 201
    disc_id = r.json()["data"]["id"]

    # 2. 生成嘉宾
    r = await client.post(f"/api/discussions/{disc_id}/panel/generate")
    assert r.status_code == 200
    gen = r.json()["data"]
    assert gen["host"]["name"]  # 有主持人
    assert len(gen["experts"]) == 3

    # 3. 编辑后确认
    r = await client.put(f"/api/discussions/{disc_id}/panel", json={
        "host": {"name": "张明（已修改）", "title": gen["host"]["title"], "stance": gen["host"]["stance"], "color": gen["host"]["color"]},
        "experts": [
            {"name": e["name"], "title": e["title"], "stance": e["stance"], "color": e["color"]}
            for e in gen["experts"]
        ],
    }, headers=session_a)
    assert r.status_code == 200
    assert r.json()["data"]["panel_confirmed"] is True
    members = r.json()["data"]["members"]
    assert members[0]["role"] == "host"
    assert members[0]["name"] == "张明（已修改）"

    # 4. 开始讨论
    r = await client.post(f"/api/discussions/{disc_id}/start", headers=session_a)
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "live"

    # 5. 暂停
    r = await client.post(f"/api/discussions/{disc_id}/pause", headers=session_a)
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "paused"

    # 6. 继续
    r = await client.post(f"/api/discussions/{disc_id}/resume", headers=session_a)
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "live"

    # 7. 推进一轮
    r = await client.post(f"/api/discussions/{disc_id}/next", headers=session_a)
    assert r.status_code == 200

    # 8. 结束
    r = await client.post(f"/api/discussions/{disc_id}/end", headers=session_a)
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "ended"

    # 9. 查看报告
    r = await client.get(f"/api/discussions/{disc_id}/report")
    assert r.status_code == 200
    report = r.json()["data"]
    assert report["discussion_id"] == disc_id
    assert len(report["panel"]) == 4  # 1 host + 3 experts
    assert report["topic"] == "人类是否应该追求永生？"

    # 10. 列表可见
    r = await client.get("/api/discussions?status=ended")
    ids = [i["id"] for i in r.json()["data"]["items"]]
    assert disc_id in ids
