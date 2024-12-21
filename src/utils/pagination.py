from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel
from fastapi import Query

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    pages: int
    has_next: bool
    has_prev: bool

class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Номер страницы"),
        page_size: int = Query(50, ge=1, le=100, description="Размер страницы")
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size

def paginate(
    items: List[T],
    total: int,
    params: PaginationParams
) -> PaginatedResponse[T]:
    """
    Создает пагинированный ответ из списка элементов
    """
    pages = (total + params.page_size - 1) // params.page_size
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=params.page,
        pages=pages,
        has_next=params.page < pages,
        has_prev=params.page > 1
    )
