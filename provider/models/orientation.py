from sqlalchemy import Column, Text, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship

from provider.models.base import Base, make_join_table

provider_orientation_table = make_join_table("provider", "orientation")


class Orientation(Base):
    """
    The way a providers practice is "oriented," that is, do they offer CBT,
    psychotherapy, etc.
    """
    body = Column(Text(), nullable=False, unique=True, index=True)

    tsv = Column(TSVECTOR)

    providers = relationship("Provider",
                             secondary=provider_orientation_table,
                             back_populates="treatment_orientations")


Index('ix_monday_orientation_body_gin',
      Orientation.tsv,
      postgresql_using="gin")

