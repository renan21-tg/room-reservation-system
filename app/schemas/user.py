from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    role: UserRole = UserRole.USER


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole

    model_config = ConfigDict(from_attributes=True)
