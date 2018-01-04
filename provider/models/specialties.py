from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from provider.models.base import make_join_table, Base

provider_speciality_table = make_join_table("provider", "specialty")


class Specialty(Base):
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

    name = Column(String(64), nullable=False)

    providers = relationship("Provider", secondary=provider_speciality_table,
                             back_populates="specialties")

    def __str__(self) -> str:
        return self.name
