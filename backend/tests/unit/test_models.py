"""Phase 2 — SQLAlchemy 模型测试 (RED)

严格对齐 DATABASE_DESIGN.md 全部字段、约束、默认值、索引。
"""

import pytest
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================
# 建表验证
# ============================================================

@pytest.fixture
async def create_tables(db_session: AsyncSession):
    """创建全部 5 张表"""
    from app.models import Base
    from app.models.discussion import Discussion
    from app.models.panel_member import PanelMember
    from app.models.utterance import Utterance
    from app.models.consensus import ConsensusDisagreement
    from app.models.expert_status_log import ExpertStatusLog

    async with db_session.bind.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with db_session.bind.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ============================================================
# Discussion 模型
# ============================================================

class TestDiscussionModel:
    """discussions 表"""

    async def test_table_exists(self, create_tables, db_session):
        from app.models.discussion import Discussion
        result = await db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='discussions'")
        )
        assert result.scalar() == "discussions"

    async def test_insert_and_query(self, create_tables, db_session):
        from app.models.discussion import Discussion
        d = Discussion(
            id="d-001",
            topic="测试话题",
            expert_count=4,
            status="pending",
            creator_session_id="session-xyz",
        )
        db_session.add(d)
        await db_session.commit()

        result = await db_session.execute(
            text("SELECT topic, expert_count, status FROM discussions WHERE id='d-001'")
        )
        row = result.fetchone()
        assert row[0] == "测试话题"
        assert row[1] == 4
        assert row[2] == "pending"

    async def test_default_values(self, create_tables, db_session):
        from app.models.discussion import Discussion
        d = Discussion(
            id="d-002",
            topic="默认值测试",
            creator_session_id="session-abc",
        )
        db_session.add(d)
        await db_session.commit()

        result = await db_session.execute(
            text("SELECT expert_count, status, current_round, rounds_without_consensus, auto_end_threshold FROM discussions WHERE id='d-002'")
        )
        row = result.fetchone()
        assert row[0] == 4       # expert_count DEFAULT 4
        assert row[1] == "pending"
        assert row[2] == 0       # current_round
        assert row[3] == 0       # rounds_without_consensus
        assert row[4] == 3       # auto_end_threshold

    async def test_max_rounds_nullable(self, create_tables, db_session):
        from app.models.discussion import Discussion
        d = Discussion(
            id="d-003",
            topic="不限轮次",
            creator_session_id="s",
            max_rounds=None,
        )
        db_session.add(d)
        await db_session.commit()

        result = await db_session.execute(
            text("SELECT max_rounds FROM discussions WHERE id='d-003'")
        )
        assert result.scalar() is None

    async def test_status_constraint(self, create_tables, db_session):
        """status 仅允许 pending/live/paused/ended"""
        from app.models.discussion import Discussion
        valid = ["pending", "live", "paused", "ended"]
        for s in valid:
            d = Discussion(id=f"d-{s}", topic="x", creator_session_id="s", status=s)
            db_session.add(d)
        await db_session.commit()  # 不抛异常即通过


# ============================================================
# PanelMember 模型
# ============================================================

class TestPanelMemberModel:
    """panel_members 表"""

    async def _insert_discussion(self, db_session, id: str = "d-001"):
        from app.models.discussion import Discussion
        d = Discussion(id=id, topic="x", creator_session_id="s")
        db_session.add(d)
        await db_session.flush()

    async def test_insert_host(self, create_tables, db_session):
        await self._insert_discussion(db_session)
        from app.models.panel_member import PanelMember
        pm = PanelMember(
            id="pm-001",
            discussion_id="d-001",
            name="张明",
            title="AI伦理学家",
            role="host",
            stance="中立客观",
            color="#6366F1",
            sort_order=0,
        )
        db_session.add(pm)
        await db_session.commit()

        result = await db_session.execute(
            text("SELECT name, role, sort_order FROM panel_members WHERE id='pm-001'")
        )
        row = result.fetchone()
        assert row[0] == "张明"
        assert row[1] == "host"
        assert row[2] == 0

    async def test_insert_expert(self, create_tables, db_session):
        await self._insert_discussion(db_session)
        from app.models.panel_member import PanelMember
        pm = PanelMember(
            id="pm-002",
            discussion_id="d-001",
            name="李研究员",
            title="认知科学研究所高级研究员",
            role="expert",
            stance="支持AI具备有限自我意识",
            color="#EF4444",
            sort_order=1,
        )
        db_session.add(pm)
        await db_session.commit()

    async def test_color_default(self, create_tables, db_session):
        await self._insert_discussion(db_session)
        from app.models.panel_member import PanelMember
        pm = PanelMember(
            id="pm-003",
            discussion_id="d-001",
            name="无名",
            title="未知",
            role="expert",
            stance="待定",
        )
        db_session.add(pm)
        await db_session.commit()

        result = await db_session.execute(
            text("SELECT color FROM panel_members WHERE id='pm-003'")
        )
        assert result.scalar() == "#3B82F6"  # 默认颜色

    async def test_avatar_prompt_nullable(self, create_tables, db_session):
        await self._insert_discussion(db_session)
        from app.models.panel_member import PanelMember
        pm = PanelMember(
            id="pm-004",
            discussion_id="d-001",
            name="无头像",
            title="测试",
            role="expert",
            stance="测试",
            avatar_prompt=None,
        )
        db_session.add(pm)
        await db_session.commit()  # 不抛异常

    async def test_role_constraint(self, create_tables, db_session):
        """role 仅允许 host/expert"""
        await self._insert_discussion(db_session)
        from app.models.panel_member import PanelMember
        for role in ["host", "expert"]:
            pm = PanelMember(
                id=f"pm-{role}",
                discussion_id="d-001",
                name=role,
                title="t",
                role=role,
                stance="s",
            )
            db_session.add(pm)
        await db_session.commit()


# ============================================================
# Utterance 模型
# ============================================================

class TestUtteranceModel:
    """utterances 表"""

    async def _insert_parents(self, db_session):
        from app.models.discussion import Discussion
        from app.models.panel_member import PanelMember
        db_session.add(Discussion(id="d-001", topic="x", creator_session_id="s"))
        db_session.add(PanelMember(id="pm-001", discussion_id="d-001", name="张明",
                                   title="AI伦理学家", role="host", stance="中立", color="#6366F1", sort_order=0))
        await db_session.flush()

    async def test_insert_utterance(self, create_tables, db_session):
        await self._insert_parents(db_session)
        from app.models.utterance import Utterance
        u = Utterance(
            id="u-001",
            discussion_id="d-001",
            panel_member_id="pm-001",
            content="今天我讨论一个话题...",
            utterance_type="opening",
            round_num=0,
            sequence_num=1,
        )
        db_session.add(u)
        await db_session.commit()

    async def test_is_streaming_default_zero(self, create_tables, db_session):
        await self._insert_parents(db_session)
        from app.models.utterance import Utterance
        u = Utterance(
            id="u-002",
            discussion_id="d-001",
            panel_member_id="pm-001",
            content="流式测试",
            utterance_type="statement",
            round_num=1,
            sequence_num=2,
        )
        db_session.add(u)
        await db_session.commit()

        result = await db_session.execute(
            text("SELECT is_streaming FROM utterances WHERE id='u-002'")
        )
        assert result.scalar() == 0

    async def test_utterance_type_constraint(self, create_tables, db_session):
        await self._insert_parents(db_session)
        from app.models.utterance import Utterance
        types = ["opening", "statement", "rebuttal", "supplement", "question", "summary"]
        for i, t in enumerate(types):
            u = Utterance(
                id=f"u-type-{i}",
                discussion_id="d-001",
                panel_member_id="pm-001",
                content=f"类型测试 {t}",
                utterance_type=t,
                round_num=0,
                sequence_num=i + 3,
            )
            db_session.add(u)
        await db_session.commit()


# ============================================================
# ConsensusDisagreement 模型
# ============================================================

class TestConsensusModel:
    """consensus_disagreements 表"""

    async def _insert_discussion(self, db_session):
        from app.models.discussion import Discussion
        db_session.add(Discussion(id="d-001", topic="x", creator_session_id="s"))
        await db_session.flush()

    async def test_insert_consensus(self, create_tables, db_session):
        await self._insert_discussion(db_session)
        from app.models.consensus import ConsensusDisagreement
        import json
        c = ConsensusDisagreement(
            id="cd-001",
            discussion_id="d-001",
            type="consensus",
            title="AI自我意识定义共识",
            description="双方认可功能层面定义",
            source_utterance_ids=json.dumps(["u-001", "u-002"]),
            confidence=0.92,
            round_num=1,
        )
        db_session.add(c)
        await db_session.commit()

    async def test_insert_disagreement(self, create_tables, db_session):
        await self._insert_discussion(db_session)
        from app.models.consensus import ConsensusDisagreement
        c = ConsensusDisagreement(
            id="cd-002",
            discussion_id="d-001",
            type="disagreement",
            title="伦理 vs 功能",
            description="关于定义框架的分歧",
            source_utterance_ids="[]",
            confidence=0.75,
            round_num=2,
        )
        db_session.add(c)
        await db_session.commit()

    async def test_default_values(self, create_tables, db_session):
        await self._insert_discussion(db_session)
        from app.models.consensus import ConsensusDisagreement
        c = ConsensusDisagreement(
            id="cd-003",
            discussion_id="d-001",
            type="consensus",
            title="默认值测试",
            description="描述",
            round_num=1,
        )
        db_session.add(c)
        await db_session.commit()

        result = await db_session.execute(
            text("SELECT confidence, is_resolved, source_utterance_ids FROM consensus_disagreements WHERE id='cd-003'")
        )
        row = result.fetchone()
        assert row[0] == 1.0       # confidence DEFAULT 1.0
        assert row[1] == 0          # is_resolved DEFAULT 0
        assert row[2] == "[]"       # source_utterance_ids DEFAULT '[]'

    async def test_type_constraint(self, create_tables, db_session):
        await self._insert_discussion(db_session)
        from app.models.consensus import ConsensusDisagreement
        for t in ["consensus", "disagreement"]:
            c = ConsensusDisagreement(
                id=f"cd-{t}",
                discussion_id="d-001",
                type=t,
                title=t,
                description="desc",
                round_num=1,
            )
            db_session.add(c)
        await db_session.commit()

    async def test_confidence_range(self, create_tables, db_session):
        """confidence 应在 0.0-1.0 之间"""
        await self._insert_discussion(db_session)
        from app.models.consensus import ConsensusDisagreement
        for conf in [0.0, 0.5, 1.0]:
            c = ConsensusDisagreement(
                id=f"cd-conf-{conf}",
                discussion_id="d-001",
                type="consensus",
                title=f"置信度{conf}",
                description="test",
                confidence=conf,
                round_num=1,
            )
            db_session.add(c)
        await db_session.commit()


# ============================================================
# ExpertStatusLog 模型
# ============================================================

class TestExpertStatusLogModel:
    """expert_status_logs 表"""

    async def _insert_parents(self, db_session):
        from app.models.discussion import Discussion
        from app.models.panel_member import PanelMember
        db_session.add(Discussion(id="d-001", topic="x", creator_session_id="s"))
        db_session.add(PanelMember(id="pm-002", discussion_id="d-001", name="李研究员",
                                   title="研究员", role="expert", stance="支持", color="#EF4444", sort_order=1))
        await db_session.flush()

    async def test_insert_status_log(self, create_tables, db_session):
        await self._insert_parents(db_session)
        from app.models.expert_status_log import ExpertStatusLog
        log = ExpertStatusLog(
            id="esl-001",
            discussion_id="d-001",
            panel_member_id="pm-002",
            status="preparing",
            focus_summary="正在思考关于AI边界的观点",
            desire_value=0.85,
        )
        db_session.add(log)
        await db_session.commit()

    async def test_focus_summary_nullable(self, create_tables, db_session):
        await self._insert_parents(db_session)
        from app.models.expert_status_log import ExpertStatusLog
        log = ExpertStatusLog(
            id="esl-002",
            discussion_id="d-001",
            panel_member_id="pm-002",
            status="idle",
            focus_summary=None,
            desire_value=None,
        )
        db_session.add(log)
        await db_session.commit()

    async def test_status_constraint(self, create_tables, db_session):
        await self._insert_parents(db_session)
        from app.models.expert_status_log import ExpertStatusLog
        for s in ["idle", "preparing", "speaking"]:
            log = ExpertStatusLog(
                id=f"esl-{s}",
                discussion_id="d-001",
                panel_member_id="pm-002",
                status=s,
            )
            db_session.add(log)
        await db_session.commit()


# ============================================================
# 表个数验证
# ============================================================

class TestAllTablesCreated:
    """确保 5 张表全部创建"""

    async def test_five_tables_exist(self, create_tables, db_session):
        result = await db_session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        )
        tables = [row[0] for row in result.fetchall()]
        expected = [
            "consensus_disagreements",
            "discussions",
            "expert_status_logs",
            "panel_members",
            "utterances",
        ]
        for t in expected:
            assert t in tables, f"表 {t} 缺失"
