from sqlalchemy import String, Column
from sqlalchemy.orm import relationship

from alembic.models.base import BaseBase, make_join_table
from alembic.models.providers import Provider

provider_credential_table = make_join_table("provider", "credential")


class Credential(BaseBase):
    """
    A providers credentials, like M.S.
    """
    name = Column(String(64))

    providers = relationship(Provider, secondary=provider_credential_table,
                             back_populates="credentials")
