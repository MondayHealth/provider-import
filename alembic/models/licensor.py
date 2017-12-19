from sqlalchemy import String, Column
from sqlalchemy.orm import relationship

from alembic.models.base import BaseBase
from alembic.models.license import License


class Licensor(BaseBase):
    name = Column(String(512))

    locale = Column(String())

    licensees = relationship(License, back_populates="licensor")
