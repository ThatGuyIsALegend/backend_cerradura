from sqlalchemy.orm import Session

from app.database.models import AccessLog


def create_access_log(db: Session, *, result: str, reason: str,
                      user_id=None, similarity: float | None = None,
                      image_path: str | None = None):
    log = AccessLog(
        result=result,
        reason=reason,
        user_id=user_id,
        similarity=similarity,
        image_path=image_path,
    )
    db.add(log)
    db.flush()
    return log


def get_access_logs(db: Session, skip: int = 0, limit: int = 50):
    return (db.query(AccessLog)
            .order_by(AccessLog.attempted_at.desc())
            .offset(skip).limit(limit).all())


def get_access_log(db: Session, log_id):
    return db.query(AccessLog).filter(AccessLog.id == log_id).first()
