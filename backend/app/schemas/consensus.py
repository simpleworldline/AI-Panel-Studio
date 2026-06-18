"""共识/分歧 Response Schema"""

from pydantic import BaseModel


class ConsensusResponse(BaseModel):
    id: str
    type: str
    title: str
    description: str
    source_utterance_ids: list[str]
    confidence: float
    is_resolved: bool
    round_num: int
