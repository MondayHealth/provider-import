from sqlalchemy import String, Column, Integer

from provider.models.base import Base


class Directory(Base):
    """

    """

    #
    name = Column(String(64), nullable=False)

    #
    short_name = Column(String(32), nullable=False)

    #
    record_limit = Column(Integer)
