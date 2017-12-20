from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from provider.models.base import BaseBase, make_join_table

provider_group_table = make_join_table("provider", "group")


class Group(BaseBase):
    """
    A cohort of people. E.g.: TBI sufferers, gay people, religious people, etc.
    """
    name = Column(String(128), nullable=False)

    providers = relationship("Provider",
                             secondary=provider_group_table,
                             back_populates="groups")
