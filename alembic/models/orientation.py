from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from alembic.models.base import BaseBase, make_join_table
from alembic.models.providers import Provider

provider_orientation_table = make_join_table("provider", "orientation")


class Orientation(BaseBase):
    """
    The way a providers practice is "oriented," that is, do they offer CBT,
    psychotherapy, etc.
    """
    name = Column(String(128), nullable=False)

    providers = relationship(Provider,
                             secondary=provider_orientation_table,
                             back_populates="treatment_orientation")
