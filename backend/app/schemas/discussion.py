"""API_CONTRACT.md §2.1 — 讨论管理 Schemas"""

from pydantic import BaseModel, Field


# ---- Request ----
class DiscussionCreate(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    expert_count: int = Field(default=4, ge=2, le=8)
    max_rounds: int | None = None


# ---- Response Items ----
class MemberPreview(BaseModel):
    name: str
    role: str


class DiscussionItem(BaseModel):
    id: str
    topic: str
    expert_count: int
    status: str
    current_round: int
    created_at: str
    member_preview: list[MemberPreview] = []


class DiscussionResponse(BaseModel):
    id: str
    topic: str
    expert_count: int
    status: str
    current_round: int
    max_rounds: int | None = None
    created_at: str
    ended_at: str | None = None
    creator_session_id: str


class DiscussionListResponse(BaseModel):
    items: list[DiscussionItem]
    total: int
    page: int
    page_size: int


# ---- Control Response ----
class DiscussionControlResponse(BaseModel):
    discussion_id: str
    status: str | None = None
    round_triggered: bool | None = None
    ended_at: str | None = None
    total_rounds: int | None = None
    total_utterances: int | None = None
