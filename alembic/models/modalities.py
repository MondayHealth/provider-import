from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from alembic.models.base import BaseBase, make_join_table
from alembic.models.providers import Provider

provider_modality_table = make_join_table("provider", "modality")


class Modality(BaseBase):
    """
    What sort of patients (couples, individuals, families, etc.)
    """
    name = Column(String(64))

    providers = relationship(Provider, secondary=provider_modality_table,
                             back_populates="modalities")
