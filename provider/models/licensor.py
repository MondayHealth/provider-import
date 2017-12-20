from sqlalchemy import String, Column
from sqlalchemy.orm import relationship

from provider.models.base import Base


class Licensor(Base):
    name = Column(String(512))

    locale = Column(String())

    licenses = relationship("License", back_populates="licensor")
