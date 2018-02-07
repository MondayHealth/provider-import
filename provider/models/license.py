from sqlalchemy import String, Column, Integer, ForeignKey, DateTime, \
    UniqueConstraint
from sqlalchemy.orm import relationship

from provider.models.base import Base
from provider.models.licensor import Licensor


class License(Base):
    number = Column(String(64), nullable=False)

    secondary_number = Column(String(8))

    granted = Column(DateTime())

    licensor_id = Column(Integer, ForeignKey("licensor.id"), nullable=False)

    licensee_id = Column(Integer, ForeignKey("provider.id"), nullable=False)

    licensor = relationship(Licensor, back_populates="licenses")

    licensee = relationship("Provider", back_populates="licenses")


UniqueConstraint(License.number, License.licensor_id, License.licensee_id)
