from sqlalchemy import String, Column, Integer

from alembic.models.base import BaseBase


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

    # ???
    original_code = Column(String(16))
