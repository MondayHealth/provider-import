from sqlalchemy import String, Column, ForeignKey, Integer, Text, Boolean, \
    DateTime

from alembic.models.base import BaseBase


class ProviderRecord(BaseBase):
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

    payor = Column(Integer, ForeignKey("payor.id"))

    # TODO: List
    accepted_plan_ids = Column(String())

    first_name = Column(String(64), nullable=False)

    last_name = Column(String(64), nullable=False)

    #
    license = Column(String(), nullable=False)

    address = Column(Integer, ForeignKey("address.id"), nullable=False)

    # TODO: List
    specialties = Column(Text())

    #
    provider = Column(Integer, ForeignKey("provider.id"))

    #
    directory = Column(Integer, ForeignKey("directory.id"))

    #
    certificate_number = Column(String())

    #
    certified = Column(Boolean())

    minimum_fee = Column(Integer())

    maximum_fee = Column(Integer())

    sliding_scale = Column(Boolean())

    free_consultation = Column(Boolean())

    # TODO: List
    services = Column(Text())

    # TODO: List
    languages = Column(Text())

    # TODO: List
    treatment_orientations = Column(Text())

    # TODO: List
    works_with_groups = Column(Text())

    # TODO: List, ranges?
    works_with_ages = Column(Text())

    website_url = Column(String(2048))

    # TODO: List
    accepted_payors = Column(Text())

    #
    license_number = Column(String())

    #
    accepting_new_patients = Column(Boolean())

    # TODO: List
    modalities = Column(Text())

    began_practice = Column(Integer())

    school = Column(String(1024))

    year_graduated = Column(Integer())

    # TODO: Enum
    license_state = Column(String())

    # TODO: Enum
    accepted_payment_methods = Column(String())

    source_updated_at = Column(DateTime)
