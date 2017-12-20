from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from provider.models.base import Base, make_join_table

provider_modality_table = make_join_table("provider", "modality")


class Modality(Base):
    """
    What sort of patients (couples, individuals, families, etc.)
    """
    name = Column(String(64))

    providers = relationship("Provider", secondary=provider_modality_table,
                             back_populates="modalities")
