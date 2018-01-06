from typing import Type

from sqlalchemy import String, Column, Integer, Text, Boolean, \
    DateTime, Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import relationship

from provider.models.accepted_payor_comment import AcceptedPayorComment, \
    provider_apc_table
from provider.models.address import Address, provider_address_table
from provider.models.base import Base
from provider.models.credential import provider_credential_table, Credential
from provider.models.degree import Degree, provider_degree_table
from provider.models.enum_array import EnumArray
from provider.models.groups import provider_group_table, Group
from provider.models.language import provider_language_table, Language
from provider.models.license import License
from provider.models.modalities import provider_modality_table, Modality
from provider.models.numericrange_array import NumericRangeArray
from provider.models.orientation import provider_orientation_table, Orientation
from provider.models.payment_methods import provider_method_table, PaymentMethod
from provider.models.phones import Phone, provider_phone_table
from provider.models.plans import provider_plan_table, Plan
from provider.models.specialties import provider_speciality_table, Specialty

AGE_RANGE_NAMES = (
    'children',
    'teens',
    'adults',
    'elders',
)


def _relate(cls: Type[DeclarativeMeta], table: Table):
    return relationship(cls.__name__,
                        secondary=table,
                        back_populates="providers")


class Provider(Base):
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

    middle_name = Column(String(64))

    last_name = Column(String(64), nullable=False)

    minimum_fee = Column(Integer())

    maximum_fee = Column(Integer())

    sliding_scale = Column(Boolean())

    free_consultation = Column(Boolean())

    website_url = Column(String(2048))

    accepting_new_patients = Column(Boolean())

    began_practice = Column(Integer())

    school = Column(String(1024))

    year_graduated = Column(Integer())

    source_updated_at = Column(DateTime)

    # TODO: List, ranges?
    works_with_ages = Column(Text())

    age_ranges = Column(NumericRangeArray(postgresql.INT4RANGE, dimensions=1))

    age_groups = Column(EnumArray(
        postgresql.ENUM(*AGE_RANGE_NAMES, name='age_range_names')))

    # Custom association
    licenses = relationship(License, back_populates="licensee")

    addresses = _relate(Address, provider_address_table)

    phone_numbers = _relate(Phone, provider_phone_table)

    credentials = _relate(Credential, provider_credential_table)

    degrees = _relate(Degree, provider_degree_table)

    payment_methods = _relate(PaymentMethod, provider_method_table)

    plans_accepted = _relate(Plan, provider_plan_table)

    specialties = _relate(Specialty, provider_speciality_table)

    languages = _relate(Language, provider_language_table)

    treatment_orientations = _relate(Orientation, provider_orientation_table)

    groups = _relate(Group, provider_group_table)

    accepted_payor_comments = _relate(AcceptedPayorComment, provider_apc_table)

    modalities = _relate(Modality, provider_modality_table)
