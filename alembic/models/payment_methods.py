from sqlalchemy import String, Column, Table, Integer, ForeignKey
from sqlalchemy.orm import relationship

from alembic.models.base import BaseBase
from alembic.models.providers import Provider

provider_method_table = Table("providers_methods",
                              Column("provider_id", Integer,
                                     ForeignKey("provider.id")),
                              Column("method_id", Integer,
                                     ForeignKey("payment_method.id")))


class PaymentMethod(BaseBase):
    __tablename__ = "payment_method"

    name = Column(String(32), nullable=False)

    providers = relationship(Provider, secondary=provider_method_table,
                             back_populates="payment_methods")
