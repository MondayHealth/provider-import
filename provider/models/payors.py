from sqlalchemy import String, Column
from sqlalchemy.orm import relationship

from provider.models.base import Base


class Payor(Base):
    """
    The name of the payor of a plan, like Anthem
    """

    #
    name = Column(String(16), nullable=False)

    plans = relationship("Plan")
