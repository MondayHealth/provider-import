from sqlalchemy import Column, String, Table, Integer, ForeignKey
from sqlalchemy.orm import relationship

from alembic.models.base import BaseBase
from alembic.models.providers import Provider

modality_provider_table = Table("modalities_providers",
                                Column("modality_id", Integer,
                                       ForeignKey("modality.id")),
                                Column("provider_id", Integer,
                                       ForeignKey("provider.id")))


class Modality(BaseBase):
    """
    What sort of patients (couples, individuals, families, etc.)
    """
    name = Column(String(64))

    providers = relationship(Provider, secondary=modality_provider_table,
                             back_populates="modalities")
