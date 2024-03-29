from typing import Type, List

from sqlalchemy import String, Column, Integer, Boolean, \
    DateTime, Table, Index
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import relationship

from provider.models.accepted_payor_comment import AcceptedPayorComment, \
    provider_apc_table
from provider.models.address import Address, provider_address_table
from provider.models.base import Base
from provider.models.credential import provider_credential_table, Credential
from provider.models.degree import Degree, provider_degree_table
from provider.models.directories import Directory, provider_directory_table
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


def _relate(cls: Type[Base], table: Table):
    return relationship(cls.__name__,
                        secondary=table,
                        back_populates="providers")


class Provider(Base):
    first_name = Column(String(64), nullable=False)

    middle_name = Column(String(64))

    last_name = Column(String(64), nullable=False, index=True)

    name_tsv = Column(TSVECTOR)

    minimum_fee = Column(Integer())

    maximum_fee = Column(Integer())

    sliding_scale = Column(Boolean())

    free_consultation = Column(Boolean())

    website_url = Column(String(2048))

    accepting_new_patients = Column(Boolean())

    began_practice = Column(Integer())

    school = Column(String(1024))

    email = Column(String(512))

    year_graduated = Column(Integer())

    source_updated_at = Column(DateTime)

    gender = Column(String(32), index=True)

    age_ranges = Column(NumericRangeArray(postgresql.INT4RANGE, dimensions=1))

    age_groups = Column(EnumArray(
        postgresql.ENUM(*AGE_RANGE_NAMES, name='age_range_names')))

    # Custom association
    licenses: List[License] = relationship(License, back_populates="licensee")

    directories: List[Directory] = _relate(Directory, provider_directory_table)

    addresses: List[Address] = _relate(Address, provider_address_table)

    phone_numbers: List[Phone] = _relate(Phone, provider_phone_table)

    credentials: List[Credential] = _relate(Credential,
                                            provider_credential_table)

    degrees: List[Degree] = _relate(Degree, provider_degree_table)

    payment_methods: List[PaymentMethod] = _relate(PaymentMethod,
                                                   provider_method_table)

    plans_accepted: List[Plan] = _relate(Plan, provider_plan_table)

    specialties = _relate(Specialty, provider_speciality_table)

    languages = _relate(Language, provider_language_table)

    treatment_orientations = _relate(Orientation, provider_orientation_table)

    groups = _relate(Group, provider_group_table)

    accepted_payor_comments = _relate(AcceptedPayorComment, provider_apc_table)

    modalities = _relate(Modality, provider_modality_table)


Index("ix_monday_provider_name_gin",
      Provider.name_tsv,
      postgresql_using="gin")

""" Something like this: 
CREATE INDEX ix_monday_provider_first_name_last_name_gin
  ON monday.provider USING GIN (first_name gin_trgm_ops, last_name gin_trgm_ops)
"""
Index("ix_monday_provider_first_name_last_name_gin",
      Provider.first_name,
      Provider.last_name,
      postgresql_using="gin",
      postgresql_ops={
          'first_name': 'gin_trgm_ops',
          'last_name': 'gin_trgm_ops'
      })
