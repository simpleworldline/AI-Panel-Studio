"""发言 Response Schema"""

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
    created_at: str
