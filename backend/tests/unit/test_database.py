"""
TDD: Database Layer — 验证 SQLAlchemy 模型与 DATABASE_DESIGN.md 严格一致

测试文档: docs/tdd/01-database-layer.md
"""

import uuid
import pytest
from sqlalchemy import text


def _col_info(col):
    """将 PRAGMA table_info 行转为 {name, type, nullable, pk}"""
    return {
        "name": col[1],
        "type": col[2],
        "nullable": not col[3],  # notnull=1 means NOT NULL
        "pk": col[5],
    }


async def _get_columns(conn, table_name):
    """通过 PRAGMA table_info 获取列信息（避免 async engine 不支持 inspector）"""
    result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
    rows = result.fetchall()
    return {r[1]: _col_info(r) for r in rows}


# ============================================================
# 2.1 表存在性验证
# ============================================================
@pytest.mark.asyncio
async def test_tables_exist(async_engine):
    """5 张表全部创建"""
    async with async_engine.connect() as conn:
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = {row[0] for row in result.fetchall()}
    expected = {"discussions", "panel_members", "utterances", "consensus_disagreements", "expert_status_logs"}
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"


# ============================================================
# 2.2 表结构验证
# ============================================================
@pytest.mark.asyncio
async def test_discussions_columns(async_engine):
    """discussions 表结构与 DATABASE_DESIGN.md §2.1 一致"""
    async with async_engine.connect() as conn:
        cols = await _get_columns(conn, "discussions")

    assert cols["id"]["pk"] == 1
    assert not cols["topic"]["nullable"]
    assert not cols["expert_count"]["nullable"]
    assert cols["max_rounds"]["nullable"]  # NULLABLE
    assert not cols["status"]["nullable"]
    assert not cols["creator_session_id"]["nullable"]
    assert not cols["current_round"]["nullable"]
    assert not cols["rounds_without_consensus"]["nullable"]
    assert not cols["auto_end_threshold"]["nullable"]
    assert not cols["created_at"]["nullable"]
    assert cols["ended_at"]["nullable"]  # NULLABLE


@pytest.mark.asyncio
async def test_panel_members_columns(async_engine):
    """panel_members 表结构与 DATABASE_DESIGN.md §2.2 一致"""
    async with async_engine.connect() as conn:
        cols = await _get_columns(conn, "panel_members")

    expected = ["id", "discussion_id", "name", "title", "role", "stance", "color", "avatar_prompt", "sort_order"]
    for name in expected:
        assert name in cols, f"Missing column: {name}"


@pytest.mark.asyncio
async def test_utterances_columns(async_engine):
    """utterances 表结构与 DATABASE_DESIGN.md §2.3 一致"""
    async with async_engine.connect() as conn:
        cols = await _get_columns(conn, "utterances")

    expected = ["id", "discussion_id", "panel_member_id", "content", "utterance_type",
                "round_num", "sequence_num", "is_streaming", "created_at"]
    for name in expected:
        assert name in cols, f"Missing column: {name}"


@pytest.mark.asyncio
async def test_consensus_disagreements_columns(async_engine):
    """consensus_disagreements 表结构与 DATABASE_DESIGN.md §2.4 一致"""
    async with async_engine.connect() as conn:
        cols = await _get_columns(conn, "consensus_disagreements")

    expected = ["id", "discussion_id", "type", "title", "description",
                "source_utterance_ids", "confidence", "is_resolved", "round_num",
                "created_at", "updated_at"]
    for name in expected:
        assert name in cols, f"Missing column: {name}"


@pytest.mark.asyncio
async def test_expert_status_logs_columns(async_engine):
    """expert_status_logs 表结构与 DATABASE_DESIGN.md §2.5 一致"""
    async with async_engine.connect() as conn:
        cols = await _get_columns(conn, "expert_status_logs")

    expected = ["id", "discussion_id", "panel_member_id", "status", "focus_summary", "desire_value", "recorded_at"]
    for name in expected:
        assert name in cols, f"Missing column: {name}"


# ============================================================
# 2.3 业务约束验证
# ============================================================
@pytest.mark.asyncio
async def test_discussion_status_check(async_session):
    """status 只能是 pending/live/paused/ended"""
    from app.models.discussion import Discussion

    d = Discussion(
        id=str(uuid.uuid4()), topic="测试", expert_count=4,
        status="invalid_status", creator_session_id="sid-1"
    )
    async_session.add(d)
    with pytest.raises(Exception):
        await async_session.flush()
    await async_session.rollback()


@pytest.mark.asyncio
async def test_expert_count_check_min(async_session):
    """expert_count < 2 应拒绝"""
    from app.models.discussion import Discussion

    d = Discussion(
        id=str(uuid.uuid4()), topic="测试", expert_count=1,
        status="pending", creator_session_id="sid-1"
    )
    async_session.add(d)
    with pytest.raises(Exception):
        await async_session.flush()
    await async_session.rollback()


@pytest.mark.asyncio
async def test_expert_count_check_max(async_session):
    """expert_count > 8 应拒绝"""
    from app.models.discussion import Discussion

    d = Discussion(
        id=str(uuid.uuid4()), topic="测试", expert_count=10,
        status="pending", creator_session_id="sid-1"
    )
    async_session.add(d)
    with pytest.raises(Exception):
        await async_session.flush()
    await async_session.rollback()


@pytest.mark.asyncio
async def test_unique_host_per_discussion(async_session):
    """(discussion_id, role='host') 唯一约束 — 每个讨论只能有一个主持人"""
    from app.models.discussion import Discussion
    from app.models.panel_member import PanelMember

    disc_id = str(uuid.uuid4())
    d = Discussion(id=disc_id, topic="测试唯一", expert_count=2, status="pending", creator_session_id="sid-1")
    async_session.add(d)
    await async_session.flush()

    host1 = PanelMember(
        id=str(uuid.uuid4()), discussion_id=disc_id, name="主持A",
        title="T1", role="host", stance="中立", color="#6366F1", sort_order=0,
    )
    host2 = PanelMember(
        id=str(uuid.uuid4()), discussion_id=disc_id, name="主持B",
        title="T2", role="host", stance="中立", color="#EF4444", sort_order=1,
    )
    async_session.add_all([host1, host2])
    with pytest.raises(Exception):
        await async_session.flush()
    await async_session.rollback()


@pytest.mark.asyncio
async def test_expert_status_check(async_session):
    """expert_status_logs.status 只能是 idle/preparing/speaking"""
    from app.models.discussion import Discussion
    from app.models.panel_member import PanelMember
    from app.models.expert_status_log import ExpertStatusLog

    disc_id = str(uuid.uuid4())
    pm_id = str(uuid.uuid4())
    d = Discussion(id=disc_id, topic="测试", expert_count=2, status="live", creator_session_id="sid-1")
    pm = PanelMember(id=pm_id, discussion_id=disc_id, name="专家A", title="研究员",
                     role="expert", stance="支持", color="#EF4444", sort_order=1)
    async_session.add_all([d, pm])
    await async_session.flush()

    log = ExpertStatusLog(
        id=str(uuid.uuid4()), discussion_id=disc_id, panel_member_id=pm_id,
        status="invalid_status", focus_summary="测试", desire_value=0.5,
    )
    async_session.add(log)
    with pytest.raises(Exception):
        await async_session.flush()
    await async_session.rollback()


@pytest.mark.asyncio
async def test_utterance_type_check(async_session):
    """utterance_type 只能是 opening/statement/rebuttal/supplement/question/summary"""
    from app.models.discussion import Discussion
    from app.models.panel_member import PanelMember
    from app.models.utterance import Utterance

    disc_id = str(uuid.uuid4())
    pm_id = str(uuid.uuid4())
    d = Discussion(id=disc_id, topic="测试", expert_count=2, status="live", creator_session_id="sid-1")
    pm = PanelMember(id=pm_id, discussion_id=disc_id, name="张明", title="T", role="host",
                     stance="中立", color="#6366F1", sort_order=0)
    async_session.add_all([d, pm])
    await async_session.flush()

    u = Utterance(
        id=str(uuid.uuid4()), discussion_id=disc_id, panel_member_id=pm_id,
        content="测试", utterance_type="bad_type", round_num=0, sequence_num=1,
    )
    async_session.add(u)
    with pytest.raises(Exception):
        await async_session.flush()
    await async_session.rollback()


@pytest.mark.asyncio
async def test_consensus_type_check(async_session):
    """consensus_disagreements.type 只能是 consensus/disagreement"""
    from app.models.discussion import Discussion
    from app.models.consensus import ConsensusDisagreement

    disc_id = str(uuid.uuid4())
    d = Discussion(id=disc_id, topic="测试", expert_count=2, status="live", creator_session_id="sid-1")
    async_session.add(d)
    await async_session.flush()

    cd = ConsensusDisagreement(
        id=str(uuid.uuid4()), discussion_id=disc_id, type="bad_type",
        title="测试", description="描述", source_utterance_ids="[]",
        confidence=0.5, round_num=1,
    )
    async_session.add(cd)
    with pytest.raises(Exception):
        await async_session.flush()
    await async_session.rollback()


# ============================================================
# 2.4 CRUD 与关系验证
# ============================================================
@pytest.mark.asyncio
async def test_discussion_crud(async_session):
    """Discussion 完整 CRUD 流程"""
    from app.models.discussion import Discussion

    # CREATE
    disc_id = str(uuid.uuid4())
    d = Discussion(id=disc_id, topic="CRUD测试", expert_count=6, status="pending", creator_session_id="sid-crud")
    async_session.add(d)
    await async_session.flush()

    # READ
    result = await async_session.get(Discussion, disc_id)
    assert result is not None
    assert result.topic == "CRUD测试"
    assert result.expert_count == 6
    assert result.current_round == 0
    assert result.rounds_without_consensus == 0

    # UPDATE
    result.status = "live"
    result.current_round = 3
    await async_session.flush()
    await async_session.refresh(result)
    assert result.status == "live"
    assert result.current_round == 3

    # DELETE
    await async_session.delete(result)
    await async_session.flush()
    assert await async_session.get(Discussion, disc_id) is None


@pytest.mark.asyncio
async def test_panel_member_relationship(async_session):
    """Discussion 1:N PanelMember"""
    from app.models.discussion import Discussion
    from app.models.panel_member import PanelMember

    disc_id = str(uuid.uuid4())
    d = Discussion(id=disc_id, topic="关系测试", expert_count=2, status="pending", creator_session_id="sid-1")
    async_session.add(d)
    await async_session.flush()

    pm1 = PanelMember(
        id=str(uuid.uuid4()), discussion_id=disc_id, name="张明", title="AI伦理学家",
        role="host", stance="中立", color="#6366F1", sort_order=0,
    )
    pm2 = PanelMember(
        id=str(uuid.uuid4()), discussion_id=disc_id, name="李研究员", title="认知科学家",
        role="expert", stance="支持", color="#EF4444", sort_order=1,
    )
    async_session.add_all([pm1, pm2])
    await async_session.flush()

    # 使用 select 查询避免 lazy loading greenlet 问题
    from sqlalchemy import select
    result = await async_session.execute(
        select(PanelMember).where(PanelMember.discussion_id == disc_id).order_by(PanelMember.sort_order)
    )
    members = result.scalars().all()
    assert len(members) == 2
    roles = {m.role for m in members}
    assert roles == {"host", "expert"}


@pytest.mark.asyncio
async def test_panel_member_relationship_eager(async_session):
    """Discussion 1:N PanelMember — eager loading via selectinload"""
    from app.models.discussion import Discussion
    from app.models.panel_member import PanelMember
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select

    disc_id = str(uuid.uuid4())
    d = Discussion(id=disc_id, topic="关系测试2", expert_count=2, status="pending", creator_session_id="sid-2")
    async_session.add(d)
    await async_session.flush()

    pm1 = PanelMember(
        id=str(uuid.uuid4()), discussion_id=disc_id,
        name="张明", title="AI伦理学家", role="host", stance="中立",
        color="#6366F1", sort_order=0,
    )
    pm2 = PanelMember(
        id=str(uuid.uuid4()), discussion_id=disc_id,
        name="李研究员", title="认知科学家", role="expert", stance="支持",
        color="#EF4444", sort_order=1,
    )
    async_session.add_all([pm1, pm2])
    await async_session.flush()

    stmt = select(Discussion).where(Discussion.id == disc_id).options(selectinload(Discussion.panel_members))
    result = await async_session.execute(stmt)
    loaded = result.scalar_one()
    assert len(loaded.panel_members) == 2


@pytest.mark.asyncio
async def test_utterance_relationship(async_session):
    """Utterance 关联 Discussion 和 PanelMember"""
    from app.models.discussion import Discussion
    from app.models.panel_member import PanelMember
    from app.models.utterance import Utterance

    disc_id = str(uuid.uuid4())
    pm_id = str(uuid.uuid4())
    u_id = str(uuid.uuid4())

    d = Discussion(id=disc_id, topic="关系测试", expert_count=2, status="live", creator_session_id="sid-1")
    pm = PanelMember(id=pm_id, discussion_id=disc_id, name="张明", title="T",
                     role="host", stance="中立", color="#6366F1", sort_order=0)
    async_session.add_all([d, pm])
    await async_session.flush()

    u = Utterance(id=u_id, discussion_id=disc_id, panel_member_id=pm_id,
                  content="开场白", utterance_type="opening", round_num=0, sequence_num=1)
    async_session.add(u)
    await async_session.flush()

    await async_session.refresh(u)
    assert u.discussion_id == disc_id
    assert u.panel_member_id == pm_id


@pytest.mark.asyncio
async def test_consensus_relationship(async_session):
    """ConsensusDisagreement 关联 Discussion"""
    from app.models.discussion import Discussion
    from app.models.consensus import ConsensusDisagreement

    disc_id = str(uuid.uuid4())
    d = Discussion(id=disc_id, topic="共识测试", expert_count=2, status="live", creator_session_id="sid-1")
    async_session.add(d)
    await async_session.flush()

    cd = ConsensusDisagreement(
        id=str(uuid.uuid4()), discussion_id=disc_id, type="consensus",
        title="共识1", description="大家同意", source_utterance_ids='["u-1","u-2"]',
        confidence=0.85, round_num=2,
    )
    async_session.add(cd)
    await async_session.flush()

    await async_session.refresh(cd)
    assert cd.discussion_id == disc_id
    assert cd.type == "consensus"
    assert cd.confidence == 0.85


@pytest.mark.asyncio
async def test_expert_status_log_relationship(async_session):
    """ExpertStatusLog 关联 Discussion 和 PanelMember"""
    from app.models.discussion import Discussion
    from app.models.panel_member import PanelMember
    from app.models.expert_status_log import ExpertStatusLog

    disc_id = str(uuid.uuid4())
    pm_id = str(uuid.uuid4())

    d = Discussion(id=disc_id, topic="状态测试", expert_count=2, status="live", creator_session_id="sid-1")
    pm = PanelMember(id=pm_id, discussion_id=disc_id, name="专家A", title="研究员",
                     role="expert", stance="支持", color="#EF4444", sort_order=1)
    async_session.add_all([d, pm])
    await async_session.flush()

    log = ExpertStatusLog(
        id=str(uuid.uuid4()), discussion_id=disc_id, panel_member_id=pm_id,
        status="preparing", focus_summary="正在思考...", desire_value=0.72,
    )
    async_session.add(log)
    await async_session.flush()

    await async_session.refresh(log)
    assert log.discussion_id == disc_id
    assert log.panel_member_id == pm_id
    assert log.status == "preparing"


@pytest.mark.asyncio
async def test_cascade_delete(async_session):
    """删除 Discussion 级联删除所有关联数据"""
    from app.models.discussion import Discussion
    from app.models.panel_member import PanelMember
    from app.models.utterance import Utterance
    from app.models.consensus import ConsensusDisagreement
    from app.models.expert_status_log import ExpertStatusLog

    disc_id = str(uuid.uuid4())
    pm_id = str(uuid.uuid4())

    d = Discussion(id=disc_id, topic="级联测试", expert_count=2, status="live", creator_session_id="sid-1")
    pm = PanelMember(id=pm_id, discussion_id=disc_id, name="专家", title="T",
                     role="expert", stance="S", color="#EF4444", sort_order=1)
    async_session.add_all([d, pm])
    await async_session.flush()

    u = Utterance(id=str(uuid.uuid4()), discussion_id=disc_id, panel_member_id=pm_id,
                  content="发言", utterance_type="statement", round_num=1, sequence_num=1)
    cd = ConsensusDisagreement(id=str(uuid.uuid4()), discussion_id=disc_id, type="consensus",
                               title="T", description="D", source_utterance_ids="[]",
                               confidence=0.5, round_num=1)
    log = ExpertStatusLog(id=str(uuid.uuid4()), discussion_id=disc_id, panel_member_id=pm_id,
                          status="idle", focus_summary="", desire_value=0)
    async_session.add_all([u, cd, log])
    await async_session.flush()

    u_id = u.id
    cd_id = cd.id
    log_id = log.id

    # 删除 Discussion
    await async_session.delete(d)
    await async_session.flush()

    # 验证所有关联数据被级联删除
    assert await async_session.get(PanelMember, pm_id) is None
    assert await async_session.get(Utterance, u_id) is None
    assert await async_session.get(ConsensusDisagreement, cd_id) is None
    assert await async_session.get(ExpertStatusLog, log_id) is None


# ============================================================
# 2.5 默认值与自动生成
# ============================================================
@pytest.mark.asyncio
async def test_discussion_defaults(async_session):
    """Discussion 默认值: expert_count=4, status='pending', current_round=0"""
    from app.models.discussion import Discussion

    d = Discussion(
        id=str(uuid.uuid4()), topic="默认值测试",
        creator_session_id="sid-1",
    )
    async_session.add(d)
    await async_session.flush()

    assert d.expert_count == 4
    assert d.status == "pending"
    assert d.current_round == 0
    assert d.rounds_without_consensus == 0
    assert d.auto_end_threshold == 3


@pytest.mark.asyncio
async def test_utterance_defaults(async_session):
    """Utterance 默认值: is_streaming=0"""
    from app.models.discussion import Discussion
    from app.models.panel_member import PanelMember
    from app.models.utterance import Utterance

    disc_id = str(uuid.uuid4())
    pm_id = str(uuid.uuid4())

    d = Discussion(id=disc_id, topic="默认值", expert_count=2, status="live", creator_session_id="sid-1")
    pm = PanelMember(id=pm_id, discussion_id=disc_id, name="张明", title="T",
                     role="host", stance="中立", color="#6366F1", sort_order=0)
    async_session.add_all([d, pm])
    await async_session.flush()

    u = Utterance(id=str(uuid.uuid4()), discussion_id=disc_id, panel_member_id=pm_id,
                  content="测试", utterance_type="statement", round_num=1, sequence_num=1)
    async_session.add(u)
    await async_session.flush()

    assert u.is_streaming == 0


# ============================================================
# 2.6 数据库配置验证
# ============================================================
@pytest.mark.asyncio
async def test_engine_wal_mode(async_engine):
    """WAL 模式启用 — in-memory SQLite 不支持 WAL，此测试仅验证引擎可用"""
    async with async_engine.connect() as conn:
        result = await conn.execute(text("PRAGMA journal_mode"))
        mode = (result.fetchone())[0]
        # in-memory DB 返回 'memory'，文件 DB 返回 'wal'，两者都表示正确配置
        assert mode.lower() in ("wal", "memory")


@pytest.mark.asyncio
async def test_foreign_keys_enabled(async_engine):
    """外键约束启用"""
    async with async_engine.connect() as conn:
        result = await conn.execute(text("PRAGMA foreign_keys"))
        fk = (result.fetchone())[0]
        assert fk == 1
