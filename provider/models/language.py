from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from provider.models.base import Base, make_join_table

provider_language_table = make_join_table("provider", "language")


class Language(Base):
    iso = Column(String(3), nullable=False, index=True, unique=True)

    name = Column(String(64), nullable=False, index=True, unique=True)

    providers = relationship("Provider",
                             secondary=provider_language_table,
                             back_populates="languages")
