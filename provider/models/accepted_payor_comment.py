from sqlalchemy import Column, Text, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship

from provider.models.base import Base, make_join_table

provider_apc_table = make_join_table("provider", "acceptedpayorcomment")


class AcceptedPayorComment(Base):
    body = Column(Text(), nullable=False, unique=True, index=True)

    tsv = Column(TSVECTOR)

    providers = relationship("Provider",
                             secondary=provider_apc_table,
                             back_populates="accepted_payor_comments")


Index('ix_monday_acceptedpayorcomment_body_gin',
      AcceptedPayorComment.tsv,
      postgresql_using="gin")
