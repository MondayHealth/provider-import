from sqlalchemy import Column, String, Table, Integer, ForeignKey
from sqlalchemy.orm import relationship

from alembic.models.base import BaseBase
from alembic.models.providers import Provider

orientation_provider_table = Table("orientation_provider",
                                   Column("orientation_id", Integer,
                                          ForeignKey("orientation.id")),
                                   Column("provider_id", Integer,
                                          ForeignKey("provider.id")))


class Orientation(BaseBase):
    """
    The way a providers practice is "oriented," that is, do they offer CBT,
    psychotherapy, etc.
    """
    name = Column(String(128), nullable=False)

    providers = relationship(Provider,
                             secondary=orientation_provider_table,
                             back_populates="treatment_orientation")
