from app.utils.time import utcnow

from app.core.attendance_constants import AttendanceStatus
from app.models.attendance import Attendance


def build_checkin_attendance(
    assignment_id: int,
    worker_profile_id: int,
    marked_by_user_id: int,
    notes: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    selfie_url: str | None = None,
    qr_code: str | None = None,
) -> Attendance:
    now = utcnow()

    return Attendance(
        assignment_id=assignment_id,
        worker_profile_id=worker_profile_id,
        attendance_date=now.date(),
        status=AttendanceStatus.PRESENT.value,
        check_in_time=now,
        check_in_latitude=latitude,
        check_in_longitude=longitude,
        check_in_selfie_url=selfie_url,
        qr_code=qr_code,
        marked_by_user_id=marked_by_user_id,
        notes=notes,
    )
