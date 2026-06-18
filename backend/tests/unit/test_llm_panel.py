"""TDD: LLM Panel Generation — 验证 generate_panel 调用 LLM"""

import importlib
import json
import pytest
from unittest.mock import patch, AsyncMock


def _get_llm_client():
    """Get the panel_service module's llm_client reference for patching"""
    mod = importlib.import_module("app.services.panel_service")
    return mod.llm_client


def _setup_db():
    """Create in-memory test DB + session"""
    import uuid
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from app.db.database import Base

    engine = create_async_engine("sqlite+aiosqlite://", echo=False, connect_args={
        "check_same_thread": False
    })
    return engine, async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _create_discussion(session, topic="测试话题", expert_count=4):
    import uuid
    from app.models.discussion import Discussion
    disc_id = str(uuid.uuid4())
    d = Discussion(id=disc_id, topic=topic, expert_count=expert_count, status="pending", creator_session_id="sid-1")
    session.add(d)
    await session.flush()
    return disc_id


@pytest.mark.asyncio
async def test_generate_panel_calls_llm():
    """generate_panel 调用 LLM，返回结构化数据"""
    engine, factory = _setup_db()
    async with engine.begin() as conn:
        await conn.run_sync(engine.sync_engine.dialect.get_table_names)
    from app.db.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        disc_id = await _create_discussion(session, "AI的社会影响", 2)

        llm = _get_llm_client()
        with patch.object(llm, "chat") as mock_chat:
            mock_chat.return_value = json.dumps({
                "host": {"name": "王博士", "title": "社会学教授", "stance": "中立客观"},
                "experts": [
                    {"name": "刘研究员", "title": "AI研究员", "stance": "支持AI"},
                    {"name": "陈主任", "title": "政策专家", "stance": "需严格监管"},
                ],
            })

            from app.services.panel_service import PanelService
            result = await PanelService.generate_panel(session, disc_id)

            # LLM was called
            mock_chat.assert_called_once()
            user_msg = mock_chat.call_args[0][0][1]["content"]
            assert "AI的社会影响" in user_msg
            assert "2" in user_msg

            # Structured output
            assert result["host"]["name"] == "王博士"
            assert result["host"]["color"].startswith("#")
            assert len(result["experts"]) == 2
            assert result["experts"][0]["color"].startswith("#")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_generate_panel_fallback_on_empty():
    """LLM 返回空字符串 → fallback"""
    engine, factory = _setup_db()
    from app.db.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        disc_id = await _create_discussion(session, expert_count=3)
        llm = _get_llm_client()
        with patch.object(llm, "chat") as m:
            m.return_value = ""
            from app.services.panel_service import PanelService
            result = await PanelService.generate_panel(session, disc_id)
            assert len(result["experts"]) == 3  # fallback matched count

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_generate_panel_fallback_on_malformed():
    """LLM 返回非法 JSON → fallback"""
    engine, factory = _setup_db()
    from app.db.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        disc_id = await _create_discussion(session, expert_count=2)
        llm = _get_llm_client()
        with patch.object(llm, "chat") as m:
            m.return_value = "```这不是JSON``` { bad stuff"
            from app.services.panel_service import PanelService
            result = await PanelService.generate_panel(session, disc_id)
            assert len(result["experts"]) == 2

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_generate_panel_llm_exception():
    """LLM 调用异常 → fallback"""
    engine, factory = _setup_db()
    from app.db.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as session:
        disc_id = await _create_discussion(session, expert_count=5)
        llm = _get_llm_client()
        with patch.object(llm, "chat") as m:
            m.side_effect = Exception("API timeout")
            from app.services.panel_service import PanelService
            result = await PanelService.generate_panel(session, disc_id)
            assert len(result["experts"]) == 5  # fallback

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
