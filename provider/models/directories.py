from sqlalchemy import String, Column, Integer

from provider.models.base import BaseBase


class Directory(BaseBase):
    """

    """

    #
    name = Column(String(64), nullable=False)

    #
    short_name = Column(String(32), nullable=False)

    #
    record_limit = Column(Integer)
