from typing import Generator, Optional

import pytest
from pydantic import BaseModel  # pylint: disable=no-name-in-module
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from fastapi_starter.crud.base import CRUDBase
from fastapi_starter.db import Base


class Hero(Base):
    __tablename__ = "hero"

    id: int = Column(Integer, primary_key=True, index=True, nullable=False)
    name: str = Column(String(256), unique=True, index=True, nullable=False)
    secret_name: str = Column(String(256), nullable=False)
    age = Column(Integer, nullable=True)


class HeroCreate(BaseModel):
    name: str
    secret_name: str
    age: Optional[int] = None


class HeroUpdate(BaseModel):
    name: Optional[str] = None
    secret_name: Optional[str] = None
    age: Optional[int] = None


class CRUDHero(CRUDBase[Hero, HeroCreate, HeroUpdate]):
    pass


@pytest.fixture(name="create_hero_table", scope="session", autouse=True)
def create_hero_table_fixture(engine: Engine) -> Generator[None, None, None]:
    with engine.begin() as conn:
        Base.metadata.create_all(conn, tables=[Hero.__table__])  # pylint: disable=no-member
    yield
    with engine.begin() as conn:
        Base.metadata.drop_all(conn, tables=[Hero.__table__])  # pylint: disable=no-member


@pytest.fixture(name="crud")
def crud_fixture() -> CRUDHero:
    return CRUDHero(Hero)


def test_create_does_not_commit_implicitly(db: Session, crud: CRUDHero) -> None:
    hero_create = HeroCreate(name="Deadpond", secret_name="Dive Wilson")

    hero_db = crud.create(db, obj_in=hero_create)

    assert hero_db.id is None


def test_create(db: Session, crud: CRUDHero) -> None:
    hero_create = HeroCreate(name="Deadpond", secret_name="Dive Wilson")

    hero_db = crud.create(db, obj_in=hero_create)
    db.commit()
    db.refresh(hero_db)
    actual_hero_db = db.execute(select(Hero).where(Hero.id == hero_db.id)).scalars().one()

    assert hero_db == actual_hero_db
    assert actual_hero_db.name == "Deadpond"
    assert actual_hero_db.secret_name == "Dive Wilson"


def test_update_does_not_commit_implicitly(db: Session, crud: CRUDHero) -> None:
    hero_db = Hero(name="Deadpond", secret_name="Dive Wilson")
    db.add(hero_db)
    db.commit()
    db.refresh(hero_db)
    hero_update = HeroUpdate(name="Deadpool", age=30)

    hero_db = crud.update(db, db_obj=hero_db, obj_in=hero_update)
    db.rollback()
    actual_hero_db = db.execute(select(Hero).where(Hero.id == hero_db.id)).scalars().one()

    assert actual_hero_db.name == "Deadpond"
    assert actual_hero_db.age is None


def test_update(db: Session, crud: CRUDHero) -> None:
    hero_db = Hero(name="Deadpond", secret_name="Dive Wilson")
    db.add(hero_db)
    db.commit()
    db.refresh(hero_db)
    hero_update = HeroUpdate(name="Deadpool", age=30)

    hero_db = crud.update(db, db_obj=hero_db, obj_in=hero_update)
    db.commit()
    db.refresh(hero_db)
    actual_hero_db = db.execute(select(Hero).where(Hero.id == hero_db.id)).scalars().one()

    assert hero_db == actual_hero_db
    assert actual_hero_db.name == "Deadpool"
    assert actual_hero_db.age == 30


def test_delete_does_not_commit_implicitly(db: Session, crud: CRUDHero) -> None:
    hero_db = Hero(name="Deadpond", secret_name="Dive Wilson")
    db.add(hero_db)
    db.commit()
    db.refresh(hero_db)

    crud.remove(db, obj_id=hero_db.id)
    db.rollback()

    assert db.execute(select(Hero).where(Hero.name == "Deadpond")).scalars().first()


def test_delete(db: Session, crud: CRUDHero) -> None:
    hero_db = Hero(name="Deadpond", secret_name="Dive Wilson")
    db.add(hero_db)
    db.commit()
    db.refresh(hero_db)

    crud.remove(db, obj_id=hero_db.id)
    db.commit()

    assert not db.execute(select(Hero).where(Hero.name == "Deadpond")).scalars().first()


def test_get(db: Session, crud: CRUDHero) -> None:
    hero_db_original = Hero(name="Deadpond", secret_name="Dive Wilson")
    db.add(hero_db_original)
    db.commit()
    db.refresh(hero_db_original)

    hero_db_queried = crud.get(db, obj_id=hero_db_original.id)

    assert hero_db_original == hero_db_queried


def test_get_not_found(db: Session, crud: CRUDHero) -> None:
    assert crud.get(db, obj_id=1) is None


@pytest.mark.parametrize(
    ("skip", "limit", "row_count"),
    [
        (0, 0, 0),
        (0, 2, 2),
        (1, 2, 2),
        (0, 3, 3),
        (2, 3, 1),
        (3, 3, 0),
    ],
)
def test_get_multi(db: Session, crud: CRUDHero, skip: int, limit: int, row_count: int) -> None:
    hero_db_1 = Hero(name="Deadpond", secret_name="Dive Wilson")
    hero_db_2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
    hero_db_3 = Hero(name="Rusty-Man", secret_name="Tommy Sharp", age=48)
    db.add_all([hero_db_1, hero_db_2, hero_db_3])
    db.commit()

    rows = crud.get_multi(db, skip=skip, limit=limit)

    assert len(rows) == row_count
