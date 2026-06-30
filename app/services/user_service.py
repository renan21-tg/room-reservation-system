from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, db: Session) -> None:
        self.repository = UserRepository(db)

    def create(self, payload: UserCreate) -> User:
        if self.repository.get_by_email(payload.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        if payload.role == UserRole.ADMIN and self.repository.count() > 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the first user can be registered as admin",
            )
        data = payload.model_dump(exclude={"password"})
        data["password_hash"] = hash_password(payload.password)
        data["role"] = payload.role.value
        return self.repository.add(User(**data))

    def list(self) -> list[User]:
        return self.repository.list()

    def get(self, user_id: int) -> User:
        user = self.repository.get(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
