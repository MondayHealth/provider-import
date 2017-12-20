from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.orm import relationship

from provider.models.base import BaseBase, make_join_table

provider_speciality_table = make_join_table("provider", "specialty")


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

    providers = relationship("Provider", secondary=provider_speciality_table,
                             back_populates="specialties")
