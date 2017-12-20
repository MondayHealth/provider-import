from sqlalchemy import String, Column
from sqlalchemy.orm import relationship

from provider.models.base import Base, make_join_table

provider_method_table = make_join_table("provider", "payment_method")


class PaymentMethod(Base):
    __tablename__ = "payment_method"

    name = Column(String(32), nullable=False)

    providers = relationship("Provider", secondary=provider_method_table,
                             back_populates="payment_methods")
