from geoalchemy2 import Geometry
from sqlalchemy import Column, String, JSON, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship

from provider.models.base import Base, make_join_table

provider_address_table = make_join_table("provider", "address")

phone_address_table = make_join_table("phone", "address")


class Address(Base):
    """
    Store raw addresses as entered, and google geocoding api responses
    """
    raw = Column(String(), index=True, unique=True)

    formatted = Column(String(), index=True)

    formatted_tsv = Column(TSVECTOR)

    geocoding_api_response = Column(JSON())

    point = Column(Geometry)

    providers = relationship("Provider", secondary=provider_address_table,
                             back_populates="addresses")

    phone_numbers = relationship("Phone", secondary=phone_address_table,
                                 back_populates="addresses")


Index('ix_monday_address_formatted_gin',
      Address.formatted_tsv,
      postgresql_using="gin")

Index('ix_monday_address_point_gist',
      Address.point,
      postgresql_using="gist")
