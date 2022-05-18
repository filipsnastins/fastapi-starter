from typing import Any

from sqlalchemy.orm import registry
from sqlalchemy.orm.decl_api import DeclarativeMeta

mapper_registry = registry()


# https://docs.sqlalchemy.org/en/14/orm/declarative_styles.html\
# #creating-an-explicit-base-non-dynamically-for-use-with-mypy-similar
class Base(metaclass=DeclarativeMeta):
    __abstract__ = True

    id: Any

    registry = mapper_registry
    metadata = mapper_registry.metadata

    __init__ = mapper_registry.constructor
