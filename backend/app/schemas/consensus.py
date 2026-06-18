"""Consensus Schema — 对齐 API_CONTRACT.md §2.4"""

from pydantic import BaseModel, Field


class ConsensusResponse(BaseModel):
    id: str
    discussion_id: str | None = None
    type: str
    title: str
    description: str
    source_utterance_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    is_resolved: bool = False
    round_num: int
    created_at: str | None = None
    updated_at: str | None = None
