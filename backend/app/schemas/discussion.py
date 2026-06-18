"""Discussion Schemas — 对齐 API_CONTRACT.md §2.1"""

from pydantic import BaseModel, Field
from typing import Any

from app.schemas.panel import PanelMemberResponse
from app.schemas.utterance import UtteranceResponse
from app.schemas.consensus import ConsensusResponse


# ── Request ──

class DiscussionCreate(BaseModel):
    topic: str = Field(min_length=1, max_length=200)
    expert_count: int = Field(ge=2, le=8, default=4)
    max_rounds: int | None = Field(default=None)


# ── Response ──

class DiscussionResponse(BaseModel):
    id: str
    topic: str
    expert_count: int
    status: str
    creator_session_id: str
    current_round: int
    rounds_without_consensus: int
    auto_end_threshold: int
    created_at: str
    ended_at: str | None = None
    max_rounds: int | None = None


class DiscussionSummary(BaseModel):
    id: str
    topic: str
    expert_count: int
    status: str
    current_round: int
    created_at: str
    member_preview: list[dict[str, str]]


class DiscussionDetailResponse(DiscussionResponse):
    panel: list[PanelMemberResponse]
    transcript: list[UtteranceResponse]
    consensus: list[dict[str, Any]]
    disagreements: list[dict[str, Any]]
