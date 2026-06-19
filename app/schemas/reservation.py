from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReservationCreate(BaseModel):
    user_id: int
    room_id: int
    starts_at: datetime
    ends_at: datetime
    purpose: str = Field(min_length=3, max_length=200)

    @model_validator(mode="after")
    def validate_time_range(self) -> "ReservationCreate":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be greater than starts_at")
        return self


class ReservationRead(BaseModel):
    id: int
    user_id: int
    room_id: int
    starts_at: datetime
    ends_at: datetime
    purpose: str
    status: str

    model_config = ConfigDict(from_attributes=True)
