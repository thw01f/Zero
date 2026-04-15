"""Database query pagination helpers."""
from typing import TypedDict

class Page(TypedDict):
    items: list
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

def paginate(query, page: int = 1, page_size: int = 20) -> Page:
    page = max(1, page)
    page_size = min(200, max(1, page_size))
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    total_pages = max(1, (total + page_size - 1) // page_size)
    return Page(items=items, total=total, page=page, page_size=page_size,
                total_pages=total_pages, has_next=page < total_pages, has_prev=page > 1)
