from sqlalchemy import Column, String, Integer, ForeignKey

from provider.models.base import Base


class Location(Base):
    # Phone number
    phone_number = Column(String(20))

    # A full address
    address = Column(Integer, ForeignKey("address.id"))
