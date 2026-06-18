"""API_CONTRACT.md §2.2 — 嘉宾阵容 Schemas"""

from pydantic import BaseModel, Field


# ---- Request ----
class PanelGenerateRequest(BaseModel):
    regenerate_member_id: str | None = None


class PanelMemberInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=100)
    stance: str = Field(..., min_length=1, max_length=200)
    color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")


class PanelConfirmRequest(BaseModel):
    host: PanelMemberInput
    experts: list[PanelMemberInput] = Field(..., min_length=0, max_length=8)


# ---- Response ----
class MemberGenerateItem(BaseModel):
    name: str
    title: str
    stance: str
    color: str
    avatar_prompt: str | None = None


class PanelGenerateResponse(BaseModel):
    host: MemberGenerateItem
    experts: list[MemberGenerateItem]


class MemberResponse(BaseModel):
    id: str
    name: str
    title: str
    role: str
    stance: str
    color: str
    avatar_prompt: str | None = None


class PanelConfirmResponse(BaseModel):
    discussion_id: str
    panel_confirmed: bool
    members: list[MemberResponse]
