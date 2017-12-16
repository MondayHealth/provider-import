from sqlalchemy import Column, String, Boolean, Integer

from alembic.models.base import BaseBase


class Specialty(BaseBase):
    """
      create_table "specialties", force: :cascade do |t|
        t.string "name", null: false
        t.datetime "created_at", null: false
        t.datetime "updated_at", null: false
        t.boolean "is_canonical", default: false, null: false
        t.integer "alias_id"
        t.index ["name"], name: "index_specialties_on_name", unique: true
      end
    """

    name = Column(String(), nullable=False)

    #
    is_canonical = Column(Boolean(), server_default=False, default=False,
                          nullable=False)

    #
    alias_id = Column(Integer())
