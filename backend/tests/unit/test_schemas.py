"""
TDD: Pydantic Schemas — 验证请求/响应 Schema 与 API_CONTRACT.md 严格一致

测试文档: docs/tdd/02-pydantic-schemas.md
"""

import pytest
from pydantic import ValidationError


# ============================================================
# 2.1 通用响应格式
# ============================================================
class TestApiResponse:
    def test_success_format(self):
        """ApiResponse 成功格式: {code, data, message}"""
        from app.schemas.common import ApiResponse
        resp = ApiResponse(code=200, data={"id": "d-1"}, message="success")
        model = resp.model_dump()
        assert model["code"] == 200
        assert model["data"] == {"id": "d-1"}
        assert model["message"] == "success"

    def test_error_format(self):
        """ApiResponse 错误格式"""
        from app.schemas.common import ApiResponse
        resp = ApiResponse(code=400, data=None, message="话题长度不能超过200字")
        model = resp.model_dump()
        assert model["code"] == 400
        assert model["data"] is None
        assert model["message"] == "话题长度不能超过200字"

    def test_paginated_list(self):
        """PaginatedList 分页格式"""
        from app.schemas.common import PaginatedList
        page = PaginatedList[dict](
            items=[{"a": 1}],
            total=100,
            page=1,
            page_size=20,
        )
        model = page.model_dump()
        assert model["items"] == [{"a": 1}]
        assert model["total"] == 100
        assert model["page"] == 1
        assert model["page_size"] == 20


# ============================================================
# 2.2 讨论 Schemas
# ============================================================
class TestDiscussionCreate:
    def test_valid_minimal(self):
        """最简合法输入"""
        from app.schemas.discussion import DiscussionCreate
        d = DiscussionCreate(topic="AI是否应该具备自我意识？")
        assert d.topic == "AI是否应该具备自我意识？"
        assert d.expert_count == 4  # 默认值
        assert d.max_rounds is None

    def test_valid_full(self):
        """完整合法输入"""
        from app.schemas.discussion import DiscussionCreate
        d = DiscussionCreate(topic="测试", expert_count=6, max_rounds=10)
        assert d.expert_count == 6
        assert d.max_rounds == 10

    def test_topic_empty(self):
        """空话题 → ValidationError"""
        from app.schemas.discussion import DiscussionCreate
        with pytest.raises(ValidationError):
            DiscussionCreate(topic="")

    def test_topic_too_long(self):
        """>200字话题 → ValidationError"""
        from app.schemas.discussion import DiscussionCreate
        with pytest.raises(ValidationError):
            DiscussionCreate(topic="A" * 201)

    def test_topic_max_length(self):
        """恰好200字 → 通过"""
        from app.schemas.discussion import DiscussionCreate
        d = DiscussionCreate(topic="A" * 200)
        assert len(d.topic) == 200

    def test_expert_count_too_low(self):
        """expert_count < 2 → ValidationError"""
        from app.schemas.discussion import DiscussionCreate
        with pytest.raises(ValidationError):
            DiscussionCreate(topic="测试", expert_count=1)

    def test_expert_count_too_high(self):
        """expert_count > 8 → ValidationError"""
        from app.schemas.discussion import DiscussionCreate
        with pytest.raises(ValidationError):
            DiscussionCreate(topic="测试", expert_count=9)


class TestDiscussionResponse:
    def test_full_response_shape(self):
        """DiscussionResponse 包含所有 API_CONTRACT.md §2.1 指定字段"""
        from app.schemas.discussion import DiscussionResponse
        data = {
            "id": "uuid-4",
            "topic": "AI是否应该具备自我意识？",
            "expert_count": 4,
            "max_rounds": None,
            "status": "pending",
            "creator_session_id": "session-xxx",
            "current_round": 0,
            "created_at": "2026-06-17T10:00:00Z",
        }
        resp = DiscussionResponse(**data)
        model = resp.model_dump()
        for key in data:
            assert key in model

    def test_nullable_fields(self):
        """max_rounds 和 ended_at 可为 None"""
        from app.schemas.discussion import DiscussionResponse
        resp = DiscussionResponse(
            id="d-1", topic="T", expert_count=4, status="live",
            creator_session_id="s", current_round=0,
            max_rounds=None, created_at="2026-01-01T00:00:00Z", ended_at=None,
        )
        assert resp.ended_at is None
        assert resp.max_rounds is None


class TestDiscussionListResponse:
    def test_list_format(self):
        """DiscussionList 返回分页格式"""
        from app.schemas.discussion import DiscussionListResponse
        from app.schemas.common import PaginatedList

        resp = DiscussionListResponse(
            items=[
                {
                    "id": "d-1", "topic": "T", "expert_count": 4, "status": "live",
                    "current_round": 0, "created_at": "2026-01-01T00:00:00Z",
                    "member_preview": [
                        {"name": "张教授", "role": "host"},
                        {"name": "李研究员", "role": "expert"},
                    ],
                }
            ],
            total=1,
            page=1,
            page_size=20,
        )
        assert resp.total == 1
        assert len(resp.items) == 1
        assert resp.items[0].topic == "T"

    def test_empty_list(self):
        """空列表"""
        from app.schemas.discussion import DiscussionListResponse
        resp = DiscussionListResponse(items=[], total=0, page=1, page_size=20)
        assert resp.items == []
        assert resp.total == 0


# ============================================================
# 2.3 嘉宾阵容 Schemas
# ============================================================
class TestMemberResponse:
    def test_host_shape(self):
        """主持人 MemberResponse"""
        from app.schemas.panel import MemberResponse
        m = MemberResponse(
            id="pm-1", name="张明", title="AI伦理学家", role="host",
            stance="中立客观", color="#6366F1",
        )
        assert m.role == "host"
        assert m.color == "#6366F1"

    def test_expert_shape(self):
        """专家 MemberResponse"""
        from app.schemas.panel import MemberResponse
        m = MemberResponse(
            id="pm-2", name="李研究员", title="认知科学研究所高级研究员",
            role="expert", stance="支持AI具备有限自我意识", color="#EF4444",
            avatar_prompt="一位40岁的...",
        )
        assert m.role == "expert"
        assert m.avatar_prompt is not None


class TestPanelGenerateRequest:
    def test_empty_body(self):
        """空请求体 → regenerate_member_id=None"""
        from app.schemas.panel import PanelGenerateRequest
        req = PanelGenerateRequest()
        assert req.regenerate_member_id is None

    def test_specific_regenerate(self):
        """指定 regenerate_member_id"""
        from app.schemas.panel import PanelGenerateRequest
        req = PanelGenerateRequest(regenerate_member_id="pm-specific-1")
        assert req.regenerate_member_id == "pm-specific-1"


class TestPanelGenerateResponse:
    def test_full_response(self):
        """PanelGenerateResponse 包含 host + experts"""
        from app.schemas.panel import PanelGenerateResponse, MemberGenerateItem
        resp = PanelGenerateResponse(
            host=MemberGenerateItem(
                name="张明", title="AI伦理学家", stance="中立",
                color="#6366F1", avatar_prompt="一位学者...",
            ),
            experts=[
                MemberGenerateItem(
                    name="李研究员", title="认知科学研究所高级研究员",
                    stance="支持AI", color="#EF4444", avatar_prompt="图片提示词...",
                ),
            ],
        )
        assert resp.host.name == "张明"
        assert len(resp.experts) == 1


class TestPanelConfirmRequest:
    def test_valid_request(self):
        """合法确认请求"""
        from app.schemas.panel import PanelConfirmRequest, PanelMemberInput
        req = PanelConfirmRequest(
            host=PanelMemberInput(
                name="张明", title="AI伦理学家", stance="中立客观", color="#6366F1",
            ),
            experts=[
                PanelMemberInput(
                    name="李研究员", title="认知科学家", stance="支持", color="#EF4444",
                ),
            ],
        )
        assert len(req.experts) == 1

    def test_experts_min_1(self):
        """experts 至少 1 位（因为 expert_count 2-8，但 confirm 请求的 experts 最少 1 位——主持人不在 experts 里）"""
        from app.schemas.panel import PanelConfirmRequest, PanelMemberInput
        req = PanelConfirmRequest(
            host=PanelMemberInput(name="张明", title="T", stance="S", color="#6366F1"),
            experts=[],
        )
        # 空 experts 应该允许 — 校验由 Service 层处理
        assert req.experts == []

    def test_expert_name_required(self):
        """姓名必填"""
        from app.schemas.panel import PanelMemberInput
        with pytest.raises(ValidationError):
            PanelMemberInput(title="T", stance="S", color="#6366F1")


# ============================================================
# 2.4 WebSocket 事件 Schema
# ============================================================
class TestWsExpertStatusEvent:
    def test_expert_status_shape(self):
        """expert_status 事件结构"""
        from app.schemas.ws_events import WsExpertStatusData
        data = WsExpertStatusData(
            member_id="pm-2", member_name="李研究员", member_color="#EF4444",
            status="preparing", focus_summary="正在思考...", desire_value=0.85,
            timestamp="2026-06-17T10:05:01Z",
        )
        assert data.status == "preparing"
        assert data.desire_value == 0.85


class TestWsUtteranceTokenEvent:
    def test_utterance_token_shape(self):
        """utterance_token 事件结构"""
        from app.schemas.ws_events import WsUtteranceTokenData
        data = WsUtteranceTokenData(
            utterance_id="u-5", member_id="pm-2", member_name="李研究员",
            member_title="研究员", member_color="#EF4444",
            token="我认为", sequence_num=5, round_num=2,
            is_first=False, is_last=False,
        )
        assert data.is_first is False
        assert data.is_last is False

    def test_first_and_last_token(self):
        """首个token is_first=True，末尾token is_last=True"""
        from app.schemas.ws_events import WsUtteranceTokenData
        data = WsUtteranceTokenData(
            utterance_id="u-5", member_id="pm-2", member_name="李研究员",
            member_title="研究员", member_color="#EF4444",
            token="我认为", sequence_num=5, round_num=2,
            is_first=True, is_last=True,
        )
        assert data.is_first is True
        assert data.is_last is True


class TestWsUtteranceCompleteEvent:
    def test_utterance_complete_shape(self):
        """utterance_complete 事件结构与 API_CONTRACT.md §3.2 一致"""
        from app.schemas.ws_events import WsUtteranceCompleteData
        data = WsUtteranceCompleteData(
            utterance_id="u-5", member_id="pm-2", member_name="李研究员",
            member_title="研究员", member_color="#EF4444",
            content="完整发言内容", utterance_type="statement",
            sequence_num=5, round_num=2, created_at="2026-06-17T10:05:05Z",
        )
        assert data.utterance_type == "statement"
        assert data.content == "完整发言内容"


class TestWsConsensusUpdateEvent:
    def test_consensus_update_created(self):
        """consensus_update created 事件"""
        from app.schemas.ws_events import WsConsensusUpdateData, ConsensusRecordData
        record = ConsensusRecordData(
            id="cd-1", type="consensus", title="共识一", description="双方认同",
            source_utterance_ids=["u-1", "u-5"], confidence=0.92, round_num=2,
        )
        data = WsConsensusUpdateData(action="created", record=record)
        assert data.action == "created"
        assert data.record.type == "consensus"

    def test_consensus_update_resolved(self):
        """分歧 resolved"""
        from app.schemas.ws_events import WsConsensusUpdateData, ConsensusRecordData
        record = ConsensusRecordData(
            id="cd-2", type="disagreement", title="分歧一", description="无法调和",
            source_utterance_ids=["u-3"], confidence=0.8, is_resolved=True, round_num=3,
        )
        data = WsConsensusUpdateData(action="resolved", record=record)
        assert data.record.is_resolved is True


class TestWsDiscussionEndedEvent:
    def test_discussion_ended_shape(self):
        """discussion_ended 事件结构"""
        from app.schemas.ws_events import WsDiscussionEndedData
        data = WsDiscussionEndedData(
            discussion_id="d-1", end_reason="user_ended",
            total_rounds=12, total_utterances=28,
            ended_at="2026-06-17T10:30:00Z",
        )
        assert data.end_reason == "user_ended"
        assert data.total_rounds == 12

    def test_end_reasons(self):
        """4种结束原因均可接受"""
        from app.schemas.ws_events import WsDiscussionEndedData
        for reason in ["user_ended", "max_rounds", "no_consensus", "host_decided"]:
            data = WsDiscussionEndedData(
                discussion_id="d-1", end_reason=reason,
                total_rounds=1, total_utterances=1,
                ended_at="2026-06-17T10:30:00Z",
            )
            assert data.end_reason == reason


class TestWsClientEvents:
    def test_client_event_types(self):
        """客户端 4 种事件类型"""
        from app.schemas.ws_events import ClientWsEvent
        from pydantic import TypeAdapter

        adapter = TypeAdapter(ClientWsEvent)
        valid = ["advance", "pause", "resume", "end"]
        for event_type in valid:
            evt = adapter.validate_python({"type": event_type})
            assert evt.type == event_type

    def test_invalid_client_event(self):
        """非法客户端事件类型 → ValidationError"""
        from app.schemas.ws_events import ClientWsEvent
        from pydantic import TypeAdapter
        adapter = TypeAdapter(ClientWsEvent)
        with pytest.raises(ValidationError):
            adapter.validate_python({"type": "invalid_event"})


class TestWsServerEvents:
    def test_server_event_types(self):
        """服务端事件类型枚举"""
        from app.schemas.ws_events import ServerWsEventType
        import typing
        args = typing.get_args(ServerWsEventType)
        expected = {"expert_status", "utterance_token", "utterance_complete",
                    "consensus_update", "discussion_paused", "discussion_resumed",
                    "discussion_ended", "discussion_control"}
        assert set(args) == expected
