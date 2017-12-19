from sqlalchemy import Table, Column, Integer, ForeignKey

from alembic.models.base import Base

providers_plans_table = Table("providers_plans",
                              Base.metadata,
                              Column("provider_id", Integer,
                                     ForeignKey("provider.id")),
                              Column("plan_id", Integer,
                                     ForeignKey("plan.id")))
