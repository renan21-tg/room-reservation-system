from pydantic import BaseModel, ConfigDict, Field


class RoomCreate(BaseModel):
    name: str
    location: str
    capacity: int = Field(gt=0)


class RoomUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    capacity: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class RoomRead(BaseModel):
    id: int
    name: str
    location: str
    capacity: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
