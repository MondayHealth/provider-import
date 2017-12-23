from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship

from provider.models.address import phone_address_table
from provider.models.base import Base, make_join_table

provider_phone_table = make_join_table("provider", "address")


class Phone(Base):
    """ A phone number that is strictly typed. """
    # Numbering plan area code
    npa = Column(Integer(), nullable=False)

    # Central office (exchange) code
    nxx = Column(Integer(), nullable=False)

    # Subscriber number or station code
    xxxx = Column(Integer(), nullable=False)

    # Extension
    extension = Column(Integer())

    providers = relationship("Provider", secondary=provider_phone_table,
                             back_populates="phone_numbers")

    addresses = relationship("Address", secondary=phone_address_table,
                             back_populates="phone_numbers")

    def __repr__(self) -> str:
        val = "({}) {}-{}".format(self.npa, self.nxx, self.xxxx)
        if self.extension is not None:
            val += " +" + str(self.extension)
        return val
