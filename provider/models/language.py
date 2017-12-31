from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from provider.models.base import Base, make_join_table

provider_language_table = make_join_table("provider", "language")


class Language(Base):
    name = Column(String(64), nullable=False)

    native = Column(Boolean(), default=False)

    providers = relationship("Provider",
                             secondary=provider_language_table,
                             back_populates="languages")
