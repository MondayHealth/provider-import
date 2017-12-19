from sqlalchemy import String, Column, Integer, Table, ForeignKey
from sqlalchemy.orm import relationship

from alembic.models.base import BaseBase, Base
from alembic.models.providers import Provider

provider_plan_table = Table("provider_plan",
                            Base.metadata,
                            Column("provider_id", Integer,
                                   ForeignKey("provider.id")),
                            Column("plan_id", Integer,
                                   ForeignKey("plan.id")))


class Plan(BaseBase):
    """
        t.integer "payor_id", null: false
        t.string "name", null: false
        t.text "url", null: false
        t.integer "record_limit"
        t.datetime "created_at", null: false
        t.datetime "updated_at", null: false
        t.string "original_code"
    """

    #
    name = Column(String(32), nullable=False)

    #
    url = Column(String(2048), nullable=False)

    #
    record_limit = Column(Integer())

    # A plan-specific code sometimes used to search the API
    original_code = Column(String(64))

    providers = relationship(Provider, secondary=provider_plan_table,
                             back_populates="accepted_plans")
