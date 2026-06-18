"""通用响应 Schema — 对齐 API_CONTRACT.md §1.3"""

from pydantic import BaseModel
from typing import Generic, TypeVar, Any

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int
    data: T | None
    message: str = "success"
    detail: str | None = None


class PaginatedList(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
