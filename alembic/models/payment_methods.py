from sqlalchemy import String, Column
from sqlalchemy.orm import relationship

from alembic.models.base import BaseBase, make_join_table
from alembic.models.providers import Provider

provider_method_table = make_join_table("provider", "payment_method")


class PaymentMethod(BaseBase):
    __tablename__ = "payment_method"

    name = Column(String(32), nullable=False)

    providers = relationship(Provider, secondary=provider_method_table,
                             back_populates="payment_methods")
