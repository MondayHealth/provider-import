from sqlalchemy import String, Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from alembic.models.base import BaseBase
from alembic.models.licensor import Licensor
from alembic.models.providers import Provider


class License(BaseBase):
    number = Column(String(64), nullable=False)

    granted = Column(DateTime())

    licensor_id = Column(Integer, ForeignKey("licensor.id"), primary_key=True)

    licensee_id = Column(Integer, ForeignKey("provider.id"), primary_key=True)

    licensor = relationship(Licensor, back_populates="licensees")

    licensee = relationship(Provider, back_populates="licenses")
