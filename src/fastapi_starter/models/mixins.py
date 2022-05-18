import datetime

from sqlalchemy import Column, DateTime


class CreatedUpdatedDateMixin:
    created_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_date = Column(DateTime, onupdate=datetime.datetime.utcnow, nullable=True)
