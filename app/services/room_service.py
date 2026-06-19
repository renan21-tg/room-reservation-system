from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.room import Room
from app.repositories.room_repository import RoomRepository
from app.schemas.room import RoomCreate, RoomUpdate


class RoomService:
    def __init__(self, db: Session) -> None:
        self.repository = RoomRepository(db)

    def create(self, payload: RoomCreate) -> Room:
        if self.repository.get_by_name(payload.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Room name already registered",
            )
        return self.repository.add(Room(**payload.model_dump()))

    def list(self, min_capacity: int | None = None) -> list[Room]:
        return self.repository.list_available(min_capacity=min_capacity)

    def get(self, room_id: int) -> Room:
        room = self.repository.get(room_id)
        if room is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        return room

    def update(self, room_id: int, payload: RoomUpdate) -> Room:
        room = self.get(room_id)
        changes = payload.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(room, field, value)
        self.repository.db.commit()
        self.repository.db.refresh(room)
        return room
