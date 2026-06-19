from typing import Generic, TypeVar

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, db: Session, model: type[ModelType]) -> None:
        self.db = db
        self.model = model

    def get(self, entity_id: int) -> ModelType | None:
        return self.db.get(self.model, entity_id)

    def list(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        return list(self.db.query(self.model).offset(skip).limit(limit).all())

    def add(self, entity: ModelType) -> ModelType:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: ModelType) -> None:
        self.db.delete(entity)
        self.db.commit()
