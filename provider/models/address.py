from sqlalchemy import Column, String, JSON
from sqlalchemy.orm import relationship

from provider.models.base import Base, make_join_table

provider_address_table = make_join_table("provider", "address")

phone_address_table = make_join_table("phone", "address")


class Address(Base):
    """
    Store raw addresses as entered, and google geocoding api responses
    """
    raw = Column(String(), index=True, unique=True)

    geocoding_api_response = Column(JSON())

    providers = relationship("Provider", secondary=provider_address_table,
                             back_populates="addresses")

    phone_numbers = relationship("Phone", secondary=phone_address_table,
                                 back_populates="addresses")
