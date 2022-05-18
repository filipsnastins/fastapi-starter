from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel  # pylint: disable=no-name-in-module
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(self, db: Session, obj_id: Any) -> Optional[ModelType]:
        return db.get(self.model, obj_id)

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return db.execute(select(self.model).offset(skip).limit(limit)).scalars().all()

    def get_all(self, db: Session) -> List[ModelType]:
        return db.execute(select(self.model)).scalars().all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in db_obj.__mapper__.attrs.keys():  # type: ignore
            if field in update_data:
                try:
                    setattr(db_obj, field, update_data[field])
                except AttributeError:
                    pass
        db.add(db_obj)
        return db_obj

    def remove(self, db: Session, *, obj_id: int) -> Optional[ModelType]:
        obj = self.get(db, obj_id)
        db.delete(obj)
        return obj
