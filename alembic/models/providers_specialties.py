from sqlalchemy import Table, Column, Integer, ForeignKey

from alembic.models.base import Base

providers_specialties_table = Table("providers_specialties",
                                    Base.metadata,
                                    Column("provider_id", Integer,
                                           ForeignKey("provider.id")),
                                    Column("specialty_id", Integer,
                                           ForeignKey("specialty.id")))
