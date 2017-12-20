from sqlalchemy import String, Column
from sqlalchemy.orm import relationship

from provider.models.base import Base, make_join_table

provider_payor_table = make_join_table("provider", "payor")


class Payor(Base):
    """

    """

    #
    name = Column(String(16), nullable=False)

    providers = relationship("Provider", secondary=provider_payor_table,
                             back_populates="accepted_payors")
