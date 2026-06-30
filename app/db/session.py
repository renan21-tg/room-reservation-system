from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base


def _set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000") 
    cursor.close()


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)

if settings.database_url.startswith("sqlite"):
    event.listen(engine, "connect", _set_sqlite_pragma)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db_and_tables() -> None:
    from app.models import reservation, room, user  
    from app.db.seed import seed_default_admin

    Base.metadata.create_all(bind=engine)
    _migrate_sqlite_dev_schema()
    with SessionLocal() as db:
        seed_default_admin(db)


def _migrate_sqlite_dev_schema() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    statements = []
    if "password_hash" not in user_columns:
        statements.append("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)")
    if "role" not in user_columns:
        statements.append("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
