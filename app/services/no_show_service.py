from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.reservation import Reservation, ReservationStatus


def cancel_no_shows(db: Session | None = None) -> int:
    own_session = db is None
    if own_session:
        db = SessionLocal()

    try:
        grace = timedelta(minutes=settings.no_show_grace_minutes)
        cutoff = datetime.now(timezone.utc) - grace

        expired = (
            db.query(Reservation)
            .filter(
                Reservation.status == ReservationStatus.APPROVED.value,
                Reservation.starts_at <= cutoff,
                Reservation.checked_in_at.is_(None),
            )
            .all()
        )

        for reservation in expired:
            reservation.status = ReservationStatus.CANCELED.value

        if expired:
            db.commit()

        return len(expired)

    except Exception:
        db.rollback()
        raise
    finally:
        if own_session:
            db.close()
