from sqlalchemy import Column, Text, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship

from provider.models.base import Base, make_join_table

provider_group_table = make_join_table("provider", "group")


class Group(Base):
    """
    A cohort of people. E.g.: TBI sufferers, gay people, religious people, etc.
    """
    body = Column(Text(), nullable=False, unique=True, index=True)

    tsv = Column(TSVECTOR)

    providers = relationship("Provider",
                             secondary=provider_group_table,
                             back_populates="groups")


Index('ix_monday_group_body_gin',
      Group.tsv,
      postgresql_using="gin")
