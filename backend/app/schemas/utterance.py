"""Utterance Schema — 对齐 API_CONTRACT.md §2.1 transcript"""

from pydantic import BaseModel


class UtteranceResponse(BaseModel):
    id: str
    panel_member_id: str
    member_name: str
    member_title: str
    member_color: str
    content: str
    utterance_type: str
    sequence_num: int
    round_num: int
    is_streaming: bool = False
    created_at: str
