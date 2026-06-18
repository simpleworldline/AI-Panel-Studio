"""API_CONTRACT.md §3 — WebSocket 事件 Schema"""

import time
from typing import Literal

from pydantic import BaseModel, Field


# ============================================================
# 服务端 → 客户端事件
# ============================================================

class WsExpertStatusData(BaseModel):
    member_id: str
    member_name: str
    member_color: str
    status: Literal["idle", "preparing", "speaking"]
    focus_summary: str | None = None
    desire_value: float | None = None
    timestamp: str


class WsUtteranceTokenData(BaseModel):
    utterance_id: str
    member_id: str
    member_name: str
    member_title: str
    member_color: str
    token: str
    sequence_num: int
    round_num: int
    is_first: bool = False
    is_last: bool = False


class WsUtteranceCompleteData(BaseModel):
    utterance_id: str
    member_id: str
    member_name: str
    member_title: str
    member_color: str
    content: str
    utterance_type: str
    sequence_num: int
    round_num: int
    created_at: str


class ConsensusRecordData(BaseModel):
    id: str
    type: Literal["consensus", "disagreement"]
    title: str
    description: str
    source_utterance_ids: list[str]
    confidence: float
    is_resolved: bool = False
    round_num: int


class WsConsensusUpdateData(BaseModel):
    action: Literal["created", "updated", "resolved"]
    record: ConsensusRecordData


class WsDiscussionEndedData(BaseModel):
    discussion_id: str
    end_reason: Literal["user_ended", "max_rounds", "no_consensus", "host_decided"]
    total_rounds: int
    total_utterances: int
    ended_at: str


class WsDiscussionPausedData(BaseModel):
    discussion_id: str
    timestamp: str


class WsDiscussionResumedData(BaseModel):
    discussion_id: str
    timestamp: str


class WsDiscussionControlData(BaseModel):
    action: str
    message: str


# ============================================================
# 客户端 → 服务端事件
# ============================================================
ClientEventType = Literal["advance", "pause", "resume", "end"]


class ClientWsEvent(BaseModel):
    type: ClientEventType


# ============================================================
# 统一 Server Event（discriminated union）
# ============================================================
ServerWsEventType = Literal[
    "expert_status", "utterance_token", "utterance_complete",
    "consensus_update", "discussion_paused", "discussion_resumed",
    "discussion_ended", "discussion_control",
]
