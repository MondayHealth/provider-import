from sqlalchemy import String, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from provider.models.base import Base, make_join_table
from provider.models.payors import Payor

provider_plan_table = make_join_table("provider", "plan")


class Plan(Base):
    """
        t.integer "payor_id", null: false
        t.string "name", null: false
        t.text "url", null: false
        t.integer "record_limit"
        t.datetime "created_at", null: false
        t.datetime "updated_at", null: false
        t.string "original_code"
    """

    payor_id = Column(Integer, ForeignKey("payor.id"), nullable=False)

    payor = relationship(Payor)

    #
    name = Column(String(128), nullable=False)

    #
    url = Column(String(2048), nullable=False)

    #
    record_limit = Column(Integer())

    # A plan-specific code sometimes used to search the API
    original_code = Column(String(64))

    providers = relationship("Provider", secondary=provider_plan_table,
                             back_populates="plans_accepted")
