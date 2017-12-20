from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from provider.models.base import Base, make_join_table

provider_orientation_table = make_join_table("provider", "orientation")


class Orientation(Base):
    """
    The way a providers practice is "oriented," that is, do they offer CBT,
    psychotherapy, etc.
    """
    name = Column(String(128), nullable=False)

    providers = relationship("Provider",
                             secondary=provider_orientation_table,
                             back_populates="treatment_orientation")
