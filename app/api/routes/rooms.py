from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.room import RoomCreate, RoomRead, RoomUpdate
from app.services.room_service import RoomService

router = APIRouter()


@router.post("", response_model=RoomRead, status_code=status.HTTP_201_CREATED)
def create_room(
    payload: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return RoomService(db).create(payload)


@router.get("", response_model=list[RoomRead])
def list_rooms(
    min_capacity: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
):
    return RoomService(db).list(min_capacity=min_capacity)


@router.get("/{room_id}", response_model=RoomRead)
def get_room(room_id: int, db: Session = Depends(get_db)):
    return RoomService(db).get(room_id)


@router.patch("/{room_id}", response_model=RoomRead)
def update_room(
    room_id: int,
    payload: RoomUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return RoomService(db).update(room_id, payload)
