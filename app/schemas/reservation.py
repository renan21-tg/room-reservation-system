from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_serializer

from app.models.reservation import ReservationStatus, RecurrenceRule

MAX_RECURRENCE_OCCURRENCES = 365


class ReservationCreate(BaseModel):
    user_id: int | None = None
    room_id: int
    starts_at: datetime
    ends_at: datetime
    purpose: str = Field(min_length=3, max_length=200)

    # Campos opcionais de recorrência
    recurrence_rule: RecurrenceRule = RecurrenceRule.NONE
    recurrence_end_date: datetime | None = None

    @model_validator(mode="after")
    def validate_time_range(self) -> "ReservationCreate":
        if self.starts_at.tzinfo is None:
            raise ValueError("starts_at must be timezone-aware (use UTC, ex: 2025-09-01T09:00:00+00:00)")
        if self.ends_at.tzinfo is None:
            raise ValueError("ends_at must be timezone-aware (use UTC, ex: 2025-09-01T11:00:00+00:00)")

        self.starts_at = self.starts_at.astimezone(timezone.utc)
        self.ends_at = self.ends_at.astimezone(timezone.utc)

        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be greater than starts_at")

        # Validações de recorrência
        if self.recurrence_rule != RecurrenceRule.NONE:
            if self.recurrence_end_date is None:
                raise ValueError(
                    "recurrence_end_date is required when recurrence_rule is set"
                )
            if self.recurrence_end_date.tzinfo is None:
                raise ValueError("recurrence_end_date must be timezone-aware")
            self.recurrence_end_date = self.recurrence_end_date.astimezone(timezone.utc)
            if self.recurrence_end_date <= self.starts_at:
                raise ValueError("recurrence_end_date must be after starts_at")

        return self


class ReservationRead(BaseModel):
    id: int
    user_id: int
    room_id: int
    starts_at: datetime
    ends_at: datetime
    purpose: str
    status: ReservationStatus
    recurrence_rule: RecurrenceRule
    recurrence_end_date: datetime | None
    parent_id: int | None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("starts_at", "ends_at", "recurrence_end_date")
    def serialize_dt(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
