from sqlalchemy import String, Column, Table, Integer, ForeignKey
from sqlalchemy.orm import relationship

from alembic.models.base import BaseBase
from alembic.models.providers import Provider

payor_provider_table = Table("payors_providers",
                             Column("payor_id", Integer,
                                    ForeignKey("payor.id")),
                             Column("provider_id", Integer,
                                    ForeignKey("provider.id")))


class Payor(BaseBase):
    """

    """

    #
    name = Column(String(16), nullable=False)

    providers = relationship(Provider, secondary=payor_provider_table,
                             back_populates="accepted_payors")
