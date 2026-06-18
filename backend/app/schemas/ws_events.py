"""WebSocket 事件 Schema — 对齐 API_CONTRACT.md §3"""

from pydantic import BaseModel, Field


class WsExpertStatusData(BaseModel):
    member_id: str
    member_name: str
    member_color: str
    status: str  # idle | preparing | speaking
    focus_summary: str | None = None
    desire_value: float = 0.0
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


class ConsensusRecord(BaseModel):
    id: str
    type: str  # consensus | disagreement
    title: str
    description: str
    source_utterance_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    is_resolved: bool = False
    round_num: int


class WsConsensusUpdateData(BaseModel):
    action: str  # created | updated | resolved
    record: ConsensusRecord


class WsDiscussionPausedData(BaseModel):
    discussion_id: str
    timestamp: str


class WsDiscussionResumedData(BaseModel):
    discussion_id: str
    timestamp: str


class WsDiscussionEndedData(BaseModel):
    discussion_id: str
    end_reason: str  # user_ended | max_rounds | no_consensus | host_decided
    total_rounds: int
    total_utterances: int
    ended_at: str
