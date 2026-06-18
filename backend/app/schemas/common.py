"""API_CONTRACT.md §1.3 — 通用响应格式"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int
    data: T | None
    message: str = "success"


class PaginatedList(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
