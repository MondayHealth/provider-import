from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from provider.models.base import BaseBase, make_join_table

provider_language_table = make_join_table("provider", "language")


class Language(BaseBase):
    name = Column(String(64), nullable=False)

    providers = relationship("Provider",
                             secondary=provider_language_table,
                             back_populates="languages")
