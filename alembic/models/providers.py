from sqlalchemy import Column, String

from alembic.models.base import BaseBase


class Provider(BaseBase):
    """
      create_table "providers", force: :cascade do |t|
        t.string "first_name", null: false
        t.string "last_name", null: false
        t.string "license", null: false
        t.datetime "created_at", null: false
        t.datetime "updated_at", null: false
        t.index ["first_name", "last_name", "license"],
            name: "index_providers_on_first_name_and_last_name_and_license",
            unique: true
      end
    """

    first_name = Column(String(64), nullable=False)

    last_name = Column(String(64), nullable=False)

    #
    license = Column(String(), nullable=False)
