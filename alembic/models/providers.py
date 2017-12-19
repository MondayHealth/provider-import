from sqlalchemy import String, Column, ForeignKey, Integer, Text, Boolean, \
    DateTime
from sqlalchemy.orm import relationship

from alembic.models.base import BaseBase
from alembic.models.groups import group_provider_table, Group
from alembic.models.language import Language, provider_language_table
from alembic.models.license import License
from alembic.models.modalities import Modality, modality_provider_table
from alembic.models.orientation import Orientation, orientation_provider_table
from alembic.models.payors import Payor, payor_provider_table
from alembic.models.plans import provider_plan_table, Plan
from alembic.models.specialties import Specialty, providers_specialties_table


def relate(cls, table):
    return relationship(cls, secondary=table, back_populates="providers")


class Provider(BaseBase):
    """
      create_table "provider_records", force: :cascade do |t|
        t.integer "payor_id"
        t.string "accepted_plan_ids"
        t.string "first_name", null: false
        t.string "last_name", null: false
        t.string "license", null: false
        t.string "address", null: false
        t.string "phone"
        t.text "specialties"
        t.datetime "created_at", null: false
        t.datetime "updated_at", null: false
        t.integer "provider_id"
        t.integer "directory_id"
        t.string "certificate_number"
        t.boolean "certified"
        t.integer "minimum_fee"
        t.integer "maximum_fee"
        t.boolean "sliding_scale"
        t.boolean "free_consultation"
        t.text "services"
        t.text "languages"
        t.text "treatment_orientations"
        t.text "works_with_groups"
        t.text "works_with_ages"
        t.text "website_url"
        t.text "accepted_payors"
        t.string "license_number"
        t.boolean "accepting_new_patients"
        t.text "modalities"
        t.integer "years_in_practice"
        t.string "school"
        t.integer "year_graduated"
        t.string "license_state"
        t.string "accepted_payment_methods"
        t.datetime "source_updated_at"
        t.index ["first_name", "last_name", "directory_id"],
            name: "first_last_directory_id", unique: true
        t.index ["first_name", "last_name", "payor_id"],
            name: "first_last_payor_id", unique: true
      end
    """

    first_name = Column(String(64), nullable=False)

    last_name = Column(String(64), nullable=False)

    # Practice qualifications or credentials
    license = Column(String(), nullable=False)

    address = Column(Integer, ForeignKey("address.id"), nullable=False)

    provider = Column(Integer, ForeignKey("provider.id"))

    directory = Column(Integer, ForeignKey("directory.id"))

    # Psychiatry board certificate number
    certificate_number = Column(String())

    # Whether or not they are certified on the ABPN database
    certified = Column(Boolean())

    minimum_fee = Column(Integer())

    maximum_fee = Column(Integer())

    sliding_scale = Column(Boolean())

    free_consultation = Column(Boolean())

    # TODO: List, ranges?
    works_with_ages = Column(Text())

    website_url = Column(String(2048))

    accepting_new_patients = Column(Boolean())

    began_practice = Column(Integer())

    school = Column(String(1024))

    year_graduated = Column(Integer())

    # TODO: List
    accepted_payment_methods = Column(String())

    source_updated_at = Column(DateTime)

    # Custom association
    licenses = relationship(License, back_populates="licensees")

    plans_accepted = relationship(Plan, provider_plan_table)

    specialties = relate(Specialty, providers_specialties_table)

    languages = relate(Language, provider_language_table)

    treatment_orientations = relate(Orientation, orientation_provider_table)

    groups = relate(Group, group_provider_table)

    accepted_payors = relate(Payor, payor_provider_table)

    modalities = relate(Modality, modality_provider_table)
