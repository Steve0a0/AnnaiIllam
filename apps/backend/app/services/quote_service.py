from app.core.statuses import QuoteStatus
from app.models.quote import Quote


def build_quote_entity(payload, user_id: int) -> Quote:
    return Quote(
        requirement_id=payload.requirement_id,
        quoted_amount=payload.quoted_amount,
        rate_per_worker=payload.rate_per_worker,
        worker_daily_rate=getattr(payload, 'worker_daily_rate', None),
        total_worker_days=payload.total_worker_days,
        advance_amount=payload.advance_amount,
        payment_model=payload.payment_model,
        valid_until=payload.valid_until,
        terms_notes=payload.terms_notes,
        internal_notes=payload.internal_notes,
        status=QuoteStatus.SENT.value,
        created_by_user_id=user_id,
    )
