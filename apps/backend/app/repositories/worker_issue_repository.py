from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.worker_issue import WorkerIssue


def create_worker_issue(db: Session, issue: WorkerIssue) -> WorkerIssue:
    db.add(issue)
    db.flush()
    return issue


def get_worker_issues_by_worker_profile_id(db: Session, worker_profile_id: int) -> list[WorkerIssue]:
    stmt = (
        select(WorkerIssue)
        .where(WorkerIssue.worker_profile_id == worker_profile_id)
        .order_by(WorkerIssue.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())
