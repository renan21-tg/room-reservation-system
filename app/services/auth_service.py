from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse


class AuthService:
    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.users.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        token = create_access_token(subject=str(user.id), role=user.role)
        return TokenResponse(access_token=token, user=user)
