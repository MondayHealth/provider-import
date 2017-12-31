from sqlalchemy import String, Column
from sqlalchemy.orm import relationship

from provider.models.base import Base, make_join_table

provider_credential_table = make_join_table("provider", "credential")


class Credential(Base):
    """
    A non-state license, certification, or registration.
    """
    name = Column(String(64), unique=True, nullable=False)

    acronym = Column(String(16))

    providers = relationship("Provider", secondary=provider_credential_table,
                             back_populates="credentials")
