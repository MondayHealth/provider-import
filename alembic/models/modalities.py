from sqlalchemy import Column, String

from alembic.models.base import BaseBase


class Modality(BaseBase):
    name = Column(String(64))
