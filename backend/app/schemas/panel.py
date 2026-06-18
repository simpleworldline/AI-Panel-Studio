"""Panel Schemas — 对齐 API_CONTRACT.md §2.2"""

from pydantic import BaseModel, Field


class PanelMemberEditable(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=100)
    role: str = Field(pattern=r"^(host|expert)$")
    stance: str = Field(max_length=200)
    color: str = Field(default="#3B82F6", pattern=r"^#[0-9a-fA-F]{6}$")


class PanelMemberResponse(PanelMemberEditable):
    id: str
    discussion_id: str | None = None
    avatar_prompt: str | None = None
    sort_order: int = 0


class PanelGenerateRequest(BaseModel):
    regenerate_member_id: str | None = None


class PanelGenerateResponse(BaseModel):
    host: PanelMemberEditable
    experts: list[PanelMemberEditable]


class PanelConfirmRequest(BaseModel):
    host: PanelMemberEditable
    experts: list[PanelMemberEditable]
