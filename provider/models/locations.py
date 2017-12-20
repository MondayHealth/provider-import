from sqlalchemy import Column, String, Integer, ForeignKey

from provider.models.base import BaseBase


class Location(BaseBase):
    # Phone number
    phone_number = Column(String(20))

    # A full address
    address = Column(Integer, ForeignKey("address.id"))
