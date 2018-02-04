from sqlalchemy import String, Column, Integer
from sqlalchemy.orm import relationship

from provider.models.base import Base, make_join_table

provider_directory_table = make_join_table("provider", "directory")


class Directory(Base):
    """

    """

    #
    name = Column(String(64), nullable=False)

    #
    short_name = Column(String(32), nullable=False)

    #
    record_limit = Column(Integer)

    providers = relationship("Provider", secondary=provider_directory_table,
                             back_populates="directories")
