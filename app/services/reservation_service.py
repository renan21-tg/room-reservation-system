from threading import Lock

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.reservation import Reservation, ReservationStatus, RecurrenceRule
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.user_repository import UserRepository
from app.schemas.reservation import ReservationCreate
from app.services.recurrence_service import generate_occurrences

reservation_creation_lock = Lock()


class ReservationService:
    def __init__(self, db: Session) -> None:
        self.repository = ReservationRepository(db)
        self.users = UserRepository(db)
        self.rooms = RoomRepository(db)

    def create(self, payload: ReservationCreate, current_user) -> Reservation:
        # ── Resolve user_id ───────────────────────────────────────────
        user_id = current_user.id
        if current_user.role == "admin" and payload.user_id is not None:
            user_id = payload.user_id
        elif payload.user_id is not None and payload.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        if self.users.get(user_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        room = self.rooms.get(payload.room_id)
        if room is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        if not room.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Room is inactive")

        # ── Gera todas as ocorrências (incluindo a primeira) ──────────
        extra_slots = generate_occurrences(
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
            rule=payload.recurrence_rule,
            end_date=payload.recurrence_end_date or payload.starts_at,
        )
        all_slots = [(payload.starts_at, payload.ends_at)] + extra_slots

        try:
            with reservation_creation_lock:
                # ── Verifica conflito em TODAS as ocorrências antes de inserir qualquer uma
                for slot_start, slot_end in all_slots:
                    if self.repository.has_conflict(payload.room_id, slot_start, slot_end):
                        raise HTTPException(
                            status_code=status.HTTP_409_CONFLICT,
                            detail=(
                                f"Room already reserved for "
                                f"{slot_start.strftime('%Y-%m-%d %H:%M')} UTC"
                            ),
                        )

                # ── Cria a reserva original (parent) ──────────────────
                base_data = {
                    "user_id": user_id,
                    "room_id": payload.room_id,
                    "starts_at": payload.starts_at,
                    "ends_at": payload.ends_at,
                    "purpose": payload.purpose,
                    "status": ReservationStatus.PENDING.value,
                    "recurrence_rule": payload.recurrence_rule.value,
                    "recurrence_end_date": payload.recurrence_end_date,
                    "parent_id": None,
                }
                parent = Reservation(**base_data)
                self.repository.db.add(parent)
                self.repository.db.flush()  # gera parent.id sem commitar ainda

                # ── Cria as ocorrências filhas ─────────────────────────
                for slot_start, slot_end in extra_slots:
                    child = Reservation(
                        user_id=user_id,
                        room_id=payload.room_id,
                        starts_at=slot_start,
                        ends_at=slot_end,
                        purpose=payload.purpose,
                        status=ReservationStatus.PENDING.value,
                        recurrence_rule=payload.recurrence_rule.value,
                        recurrence_end_date=payload.recurrence_end_date,
                        parent_id=parent.id,
                    )
                    self.repository.db.add(child)

                self.repository.db.commit()
                self.repository.db.refresh(parent)
                return parent  # Retorna apenas a reserva original

        except HTTPException:
            self.repository.db.rollback()
            raise
        except Exception as exc:
            self.repository.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error",
            ) from exc

    def list(self, current_user, user_id: int | None = None) -> list[Reservation]:
        if current_user.role != "admin":
            return self.repository.list_by_user(current_user.id)
        if user_id is not None:
            return self.repository.list_by_user(user_id)
        return self.repository.list()

    def get(self, reservation_id: int) -> Reservation:
        reservation = self.repository.get(reservation_id)
        if reservation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reservation not found",
            )
        return reservation

    def cancel(self, reservation_id: int, current_user) -> Reservation:
        reservation = self.get(reservation_id)
        if current_user.role != "admin" and reservation.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        reservation.status = ReservationStatus.CANCELED.value
        self.repository.db.commit()
        self.repository.db.refresh(reservation)
        return reservation

    def approve(self, reservation_id: int) -> Reservation:
        reservation = self.get(reservation_id)
        if reservation.status != ReservationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending reservations can be approved",
            )
        reservation.status = ReservationStatus.APPROVED.value
        self.repository.db.commit()
        self.repository.db.refresh(reservation)
        return reservation

    def reject(self, reservation_id: int) -> Reservation:
        reservation = self.get(reservation_id)
        if reservation.status != ReservationStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending reservations can be rejected",
            )
        reservation.status = ReservationStatus.REJECTED.value
        self.repository.db.commit()
        self.repository.db.refresh(reservation)
        return reservation
