"""Phase 10 — 集成测试

验证完整 REST API 生命周期，对齐 API_CONTRACT.md
使用 memory DB 隔离。
"""

import pytest
from httpx import AsyncClient, ASGITransport


def _fk_pragma(dbapi_conn, _record):
    c = dbapi_conn.cursor()
    c.execute("PRAGMA foreign_keys=ON")
    c.close()


@pytest.fixture
async def app():
    from app.db import session as db_session
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    from sqlalchemy import event
    event.listen(engine.sync_engine, "connect", _fk_pragma)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    db_session._session_factory = factory
    db_session._engine = engine

    from app.main import create_app
    app = create_app()

    from app.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield app

    await engine.dispose()


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


SESSION = "integration-test-session"


class TestFullLifecycle:
    """完整讨论生命周期"""

    async def test_create_discussion(self, client):
        resp = await client.post(
            "/api/discussions",
            json={"topic": "AI是否应该具备自我意识？", "expert_count": 4, "max_rounds": None},
            headers={"X-Session-Id": SESSION},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["code"] == 201
        assert data["data"]["status"] == "pending"

    async def test_full_flow(self, client):
        # CREATE
        resp = await client.post(
            "/api/discussions",
            json={"topic": "量子计算何时改变生活？", "expert_count": 3},
            headers={"X-Session-Id": SESSION},
        )
        assert resp.status_code == 201
        d_id = resp.json()["data"]["id"]

        # LIST
        resp = await client.get("/api/discussions")
        assert resp.status_code == 200
        assert len(resp.json()["data"]["items"]) >= 1

        # DETAIL
        resp = await client.get(f"/api/discussions/{d_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["topic"] == "量子计算何时改变生活？"

        # END
        resp = await client.post(f"/api/discussions/{d_id}/end", headers={"X-Session-Id": SESSION})
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "ended"

        # REPORT
        resp = await client.get(f"/api/discussions/{d_id}/report")
        assert resp.status_code == 200


class TestPermission:
    """权限校验"""

    async def test_non_creator_cannot_control(self, client):
        resp = await client.post(
            "/api/discussions",
            json={"topic": "权限测试", "expert_count": 2},
            headers={"X-Session-Id": SESSION},
        )
        d_id = resp.json()["data"]["id"]

        resp = await client.post(
            f"/api/discussions/{d_id}/end",
            headers={"X-Session-Id": "other-session"},
        )
        assert resp.json()["code"] == 40301

    async def test_cannot_end_already_ended(self, client):
        resp = await client.post(
            "/api/discussions",
            json={"topic": "重复结束测试", "expert_count": 2},
            headers={"X-Session-Id": SESSION},
        )
        d_id = resp.json()["data"]["id"]
        await client.post(f"/api/discussions/{d_id}/end", headers={"X-Session-Id": SESSION})
        resp = await client.post(f"/api/discussions/{d_id}/end", headers={"X-Session-Id": SESSION})
        assert resp.json()["code"] == 40901


class TestValidation:
    """请求校验"""

    async def test_nonexistent_discussion(self, client):
        resp = await client.get("/api/discussions/nonexistent-id")
        assert resp.json()["code"] == 40401


class TestHealth:
    """健康检查"""

    async def test_health(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "ok"
