from sqlalchemy import Column, String, Table, Integer, ForeignKey
from sqlalchemy.orm import relationship

from alembic.models.base import BaseBase
from alembic.models.providers import Provider

group_provider_table = Table("groups_providers",
                             Column("group_id", Integer,
                                    ForeignKey("orientation.id")),
                             Column("provider_id", Integer,
                                    ForeignKey("provider.id")))


class Group(BaseBase):
    """
    A cohort of people. E.g.: TBI sufferers, gay people, religious people, etc.
    """
    name = Column(String(128), nullable=False)

    providers = relationship(Provider,
                             secondary=group_provider_table,
                             back_populates="groups")
