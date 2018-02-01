from sqlalchemy import Column, Integer, Index, Boolean
from sqlalchemy.orm import relationship

from provider.models.address import phone_address_table
from provider.models.base import Base, make_join_table

provider_phone_table = make_join_table("provider", "phone")


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

    directory = Column(Integer())

    providers = relationship("Provider", secondary=provider_phone_table,
                             back_populates="phone_numbers")

    addresses = relationship("Address", secondary=phone_address_table,
                             back_populates="phone_numbers")

    def __repr__(self) -> str:
        val = "({}) {}-{}".format(self.npa, self.nxx, self.xxxx)
        if self.extension is not None:
            val += " +" + str(self.extension)
        return val


Index("ix_monday_phone_npa_nxx_xxxx_extension",
      Phone.npa,
      Phone.nxx,
      Phone.xxxx,
      Phone.extension,
      unique=True)

# Nulls are not compared so you could add the same npa-nxx-xxxx if ext is null
# Solve this with a secondary index
Index("ix_monday_phone_npa_nxx_xxxx_null",
      Phone.npa,
      Phone.nxx,
      Phone.xxxx,
      unique=True,
      postgresql_where=Phone.extension.is_(None))
