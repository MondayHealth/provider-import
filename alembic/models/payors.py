from sqlalchemy import String, Column

from alembic.models.base import BaseBase


class Payor(BaseBase):
    """

    """

    #
    name = Column(String(16), nullable=False)
