from app.models.room import Room
from app.repositories.base import BaseRepository


class RoomRepository(BaseRepository[Room]):
    def __init__(self, db) -> None:
        super().__init__(db, Room)

    def get_by_name(self, name: str) -> Room | None:
        return self.db.query(Room).filter(Room.name == name).first()

    def list_available(self, min_capacity: int | None = None) -> list[Room]:
        query = self.db.query(Room).filter(Room.is_active.is_(True))
        if min_capacity is not None:
            query = query.filter(Room.capacity >= min_capacity)
        return list(query.order_by(Room.name).all())
