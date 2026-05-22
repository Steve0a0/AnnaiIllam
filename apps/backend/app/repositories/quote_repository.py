from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.quote import Quote


def create_quote(db: Session, quote: Quote) -> Quote:
    db.add(quote)
    db.flush()
    return quote


def get_quote_by_id(db: Session, quote_id: int) -> Quote | None:
    stmt = select(Quote).where(Quote.id == quote_id)
    return db.execute(stmt).scalar_one_or_none()


def get_quote_by_requirement_id(db: Session, requirement_id: int) -> Quote | None:
    stmt = select(Quote).where(Quote.requirement_id == requirement_id).order_by(Quote.created_at.desc())
    return db.execute(stmt).scalars().first()
