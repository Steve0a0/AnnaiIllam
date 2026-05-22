"""
Pagination helpers.

All list endpoints that can return large datasets should use these utilities.

Usage in a route:
    from app.utils.pagination import PaginationParams, paginate_query

    @router.get("")
    def list_items(
        pg: PaginationParams = Depends(),
        ...
    ):
        items, total = paginate_query(stmt, db, pg)
        return success_response("...", {"items": [...], "total": total, "page": pg.page, "page_size": pg.page_size})
"""

from fastapi import Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(50, ge=1, le=200, description="Items per page (max 200)"),
    ):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def paginate(stmt, db: Session, pg: PaginationParams):
    """
    Execute `stmt` with pagination.  Returns (items, total_count).

    `stmt` must be a SQLAlchemy select() statement.
    """
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar_one()

    paginated_stmt = stmt.limit(pg.page_size).offset(pg.offset)
    items = list(db.execute(paginated_stmt).scalars().all())

    return items, total


def pagination_meta(pg: PaginationParams, total: int) -> dict:
    return {
        "page": pg.page,
        "page_size": pg.page_size,
        "total": total,
        "total_pages": max(1, (total + pg.page_size - 1) // pg.page_size),
    }
