from sqlalchemy import String, Column, Table, Integer, ForeignKey
from sqlalchemy.orm import relationship

from alembic.models.base import BaseBase
from alembic.models.providers import Provider

provider_credential_table = Table("providers_credentials",
                                  Column("provider_id", Integer,
                                         ForeignKey("provider.id")),
                                  Column("credential_id", Integer,
                                         ForeignKey("credential.id")))


class Credential(BaseBase):
    """
    A providers credentials, like M.S.
    """
    name = Column(String(64))

    providers = relationship(Provider, secondary=provider_credential_table,
                             back_populates="credentials")
