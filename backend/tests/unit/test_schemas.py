"""Phase 7 — Pydantic Schemas 测试 (RED)

严格对齐 API_CONTRACT.md 请求/响应格式。
所有字段名 snake_case (Python 后端标准)。
"""

import pytest
from datetime import datetime, timezone


class TestCommonSchemas:
    """ApiResponse + PaginatedList"""

    def test_api_response_success(self):
        from app.schemas.common import ApiResponse
        resp = ApiResponse(code=200, data={"id": "d-1"}, message="success")
        d = resp.model_dump()
        assert d["code"] == 200
        assert d["data"]["id"] == "d-1"
        assert d["message"] == "success"

    def test_api_response_error(self):
        from app.schemas.common import ApiResponse
        resp = ApiResponse(code=400, data=None, message="话题太长", detail="validation_error")
        d = resp.model_dump()
        assert d["code"] == 400
        assert d["data"] is None
        assert d["detail"] == "validation_error"

    def test_paginated_list(self):
        from app.schemas.common import PaginatedList
        from app.schemas.discussion import DiscussionSummary
        items = [
            DiscussionSummary(
                id="d-1", topic="A", expert_count=4, status="live",
                current_round=1, created_at="2026-01-01T00:00:00Z",
                member_preview=[{"name": "张明", "role": "host", "color": "#6366F1"}],
            )
        ]
        page = PaginatedList(items=items, total=1, page=1, page_size=20)
        d = page.model_dump()
        assert len(d["items"]) == 1
        assert d["total"] == 1


class TestDiscussionSchemas:
    """Discussion create/response/list"""

    def test_create_discussion_request(self):
        from app.schemas.discussion import DiscussionCreate
        req = DiscussionCreate(
            topic="AI是否应该具备自我意识？",
            expert_count=4,
            max_rounds=None,
        )
        d = req.model_dump()
        assert d["topic"] == "AI是否应该具备自我意识？"
        assert d["expert_count"] == 4
        assert d["max_rounds"] is None

    def test_topic_length_validation(self):
        from app.schemas.discussion import DiscussionCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            DiscussionCreate(topic="", expert_count=4)
        with pytest.raises(ValidationError):
            DiscussionCreate(topic="A" * 201, expert_count=4)

    def test_expert_count_range(self):
        from app.schemas.discussion import DiscussionCreate
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            DiscussionCreate(topic="Test", expert_count=1)
        with pytest.raises(ValidationError):
            DiscussionCreate(topic="Test", expert_count=9)

    def test_discussion_response(self):
        from app.schemas.discussion import DiscussionResponse
        resp = DiscussionResponse(
            id="d-1",
            topic="Test",
            expert_count=4,
            status="pending",
            creator_session_id="s-1",
            current_round=0,
            rounds_without_consensus=0,
            auto_end_threshold=3,
            created_at=datetime.now(timezone.utc).isoformat(),
            ended_at=None,
        )
        d = resp.model_dump()
        assert d["id"] == "d-1"

    def test_discussion_detail_response(self):
        from app.schemas.discussion import DiscussionDetailResponse
        from app.schemas.panel import PanelMemberResponse
        from app.schemas.utterance import UtteranceResponse
        now = datetime.now(timezone.utc).isoformat()
        detail = DiscussionDetailResponse(
            id="d-1", topic="Test", expert_count=4, status="live",
            creator_session_id="s", current_round=2, rounds_without_consensus=0,
            auto_end_threshold=3, created_at=now, ended_at=None,
            max_rounds=None,
            panel=[
                PanelMemberResponse(
                    id="pm-1", discussion_id="d-1", name="张明", title="AI伦理学家",
                    role="host", stance="中立", color="#6366F1", avatar_prompt=None, sort_order=0,
                )
            ],
            transcript=[
                UtteranceResponse(
                    id="u-1", panel_member_id="pm-1", member_name="张明",
                    member_title="AI伦理学家", member_color="#6366F1",
                    content="开场发言", utterance_type="opening",
                    sequence_num=1, round_num=0, is_streaming=False, created_at=now,
                )
            ],
            consensus=[], disagreements=[],
        )
        assert detail.status == "live"
        assert len(detail.panel) == 1


class TestPanelSchemas:
    """Panel generate/confirm request/response"""

    def test_panel_generate_request(self):
        from app.schemas.panel import PanelGenerateRequest
        req = PanelGenerateRequest(regenerate_member_id=None)
        assert req.regenerate_member_id is None
        req2 = PanelGenerateRequest(regenerate_member_id="pm-1")
        assert req2.regenerate_member_id == "pm-1"

    def test_panel_generate_response(self):
        from app.schemas.panel import PanelGenerateResponse, PanelMemberEditable
        resp = PanelGenerateResponse(
            host=PanelMemberEditable(name="张明", title="AI伦理学家", role="host", stance="中立", color="#6366F1"),
            experts=[
                PanelMemberEditable(name="李研究员", title="研究员", role="expert", stance="支持", color="#EF4444"),
            ],
        )
        d = resp.model_dump()
        assert d["host"]["name"] == "张明"
        assert len(d["experts"]) == 1

    def test_panel_confirm_request(self):
        from app.schemas.panel import PanelConfirmRequest, PanelMemberEditable
        req = PanelConfirmRequest(
            host=PanelMemberEditable(name="张明", title="AI伦理学家", role="host", stance="中立", color="#6366F1"),
            experts=[
                PanelMemberEditable(name="李研究员", title="研究员", role="expert", stance="支持", color="#EF4444"),
            ],
        )
        d = req.model_dump()
        assert d["host"]["color"] == "#6366F1"


class TestUtteranceSchemas:
    """UtteranceResponse"""

    def test_utterance_response(self):
        from app.schemas.utterance import UtteranceResponse
        now = datetime.now(timezone.utc).isoformat()
        resp = UtteranceResponse(
            id="u-1", panel_member_id="pm-1", member_name="张明",
            member_title="AI伦理学家", member_color="#6366F1",
            content="发言内容", utterance_type="statement",
            sequence_num=3, round_num=1, is_streaming=False, created_at=now,
        )
        d = resp.model_dump()
        assert d["member_name"] == "张明"
        assert d["utterance_type"] == "statement"


class TestWebSocketSchemas:
    """WebSocket 事件 Schema"""

    def test_expert_status_event(self):
        from app.schemas.ws_events import WsExpertStatusData
        data = WsExpertStatusData(
            member_id="pm-1", member_name="李研究员", member_color="#EF4444",
            status="preparing", focus_summary="正在分析...", desire_value=0.85,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        d = data.model_dump()
        assert d["status"] == "preparing"
        assert d["desire_value"] == 0.85

    def test_utterance_token_event(self):
        from app.schemas.ws_events import WsUtteranceTokenData
        data = WsUtteranceTokenData(
            utterance_id="u-1", member_id="pm-1", member_name="李",
            member_title="研究员", member_color="#EF4444", token="我认为",
            sequence_num=3, round_num=1, is_first=True, is_last=False,
        )
        d = data.model_dump()
        assert d["token"] == "我认为"
        assert d["is_first"] is True

    def test_utterance_complete_event(self):
        from app.schemas.ws_events import WsUtteranceCompleteData
        now = datetime.now(timezone.utc).isoformat()
        data = WsUtteranceCompleteData(
            utterance_id="u-1", member_id="pm-1", member_name="李",
            member_title="研究员", member_color="#EF4444",
            content="完整发言", utterance_type="statement",
            sequence_num=3, round_num=1, created_at=now,
        )
        assert data.content == "完整发言"

    def test_consensus_update_event(self):
        from app.schemas.ws_events import WsConsensusUpdateData, ConsensusRecord
        now = datetime.now(timezone.utc).isoformat()
        record = ConsensusRecord(
            id="cd-1", type="consensus", title="共识标题",
            description="描述", source_utterance_ids=["u-1", "u-2"],
            confidence=0.92, round_num=2,
        )
        data = WsConsensusUpdateData(
            action="created", record=record,
        )
        assert data.record.confidence == 0.92
        assert data.record.is_resolved is False

    def test_discussion_ended_event(self):
        from app.schemas.ws_events import WsDiscussionEndedData
        data = WsDiscussionEndedData(
            discussion_id="d-1", end_reason="max_rounds",
            total_rounds=5, total_utterances=12,
            ended_at=datetime.now(timezone.utc).isoformat(),
        )
        assert data.end_reason in ("user_ended", "max_rounds", "no_consensus", "host_decided")
