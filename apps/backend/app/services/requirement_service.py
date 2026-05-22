from app.core.statuses import RequirementStatus
from app.models.requirement import Requirement


def build_requirement_entity(payload, client_id: int, user_id: int) -> Requirement:
    return Requirement(
        client_id=client_id,
        category=payload.category,
        subcategory=payload.subcategory,
        number_of_workers=payload.number_of_workers,
        work_location=payload.work_location,
        city=payload.city,
        state=payload.state,
        start_date=payload.start_date,
        duration_days=payload.duration_days,
        shift_details=payload.shift_details,
        food_required=payload.food_required,
        accommodation_required=payload.accommodation_required,
        budget_amount=payload.budget_amount,
        notes=payload.notes,
        status=RequirementStatus.SUBMITTED.value,
        created_by_user_id=user_id,
    )
