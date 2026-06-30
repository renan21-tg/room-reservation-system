from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole

DEFAULT_ADMIN_EMAIL = "admin@email.com"
DEFAULT_ADMIN_PASSWORD = "admin123"


def seed_default_admin(db: Session) -> User:
    admin = db.query(User).filter(User.email == DEFAULT_ADMIN_EMAIL).first()
    if admin is None:
        admin = User(
            name="admin",
            email=DEFAULT_ADMIN_EMAIL,
            password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            role=UserRole.ADMIN.value,
        )
        db.add(admin)
    else:
        admin.name = "admin"
        admin.password_hash = hash_password(DEFAULT_ADMIN_PASSWORD)
        admin.role = UserRole.ADMIN.value

    db.commit()
    db.refresh(admin)
    return admin
