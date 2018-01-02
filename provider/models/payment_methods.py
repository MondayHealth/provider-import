from enum import Enum as BuitinEnum
from enum import auto

from sqlalchemy import Column, Enum
from sqlalchemy.orm import relationship

from provider.models.base import Base, make_join_table

provider_method_table = make_join_table("provider", "payment_method")


class PaymentMethodType(BuitinEnum):
    cash = auto()
    check = auto()
    wire = auto()
    ach = auto()

    hsa = auto()

    amex = auto()
    discover = auto()
    mastercard = auto()
    visa = auto()

    paypal = auto()
    venmo = auto()
    apple = auto()
    android = auto()


class PaymentMethod(Base):
    __tablename__ = "payment_method"

    payment_type = Column(Enum(PaymentMethodType), unique=True, nullable=False)

    providers = relationship("Provider",
                             secondary=provider_method_table,
                             back_populates="payment_methods")
