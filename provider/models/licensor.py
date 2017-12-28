from sqlalchemy import String, Column, Index
from sqlalchemy.orm import relationship

from provider.models.base import Base


class Licensor(Base):
    name = Column(String(512))
    country = Column(String(3), nullable=False, default="USA")
    state = Column(String(2))
    city = Column(String(64))

    licenses = relationship("License", back_populates="licensor")


Index("ix_monday_licensor_name_country_state_city",
      Licensor.name,
      Licensor.country,
      Licensor.state,
      Licensor.city,
      unique=True)
