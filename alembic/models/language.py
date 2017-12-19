from sqlalchemy import Column, String, Table, Integer, ForeignKey
from sqlalchemy.orm import relationship

from alembic.models.base import BaseBase
from alembic.models.providers import Provider

provider_language_table = Table("provider_language",
                                Column("provider_id", Integer,
                                       ForeignKey("provider.id")),
                                Column("language_id", Integer,
                                       ForeignKey("language.id")))


class Language(BaseBase):
    name = Column(String(64), nullable=False)

    providers = relationship(Provider,
                             secondary=provider_language_table,
                             back_populates="languages")
