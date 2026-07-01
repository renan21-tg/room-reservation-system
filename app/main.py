from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import auth, reservations, rooms, users
from app.db.session import create_db_and_tables
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    create_db_and_tables()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Sistema de Reserva de Salas",
    version="0.1.0",
    description="API REST para gerenciar salas, usuarios e reservas.",
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
app.include_router(reservations.router, prefix="/reservations", tags=["reservations"])
