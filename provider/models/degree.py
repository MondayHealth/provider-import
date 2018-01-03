from sqlalchemy import Column, String, UniqueConstraint, Enum
from sqlalchemy.orm import relationship

from fixtures.academic_degrees import EducationLevel
from provider.models.base import Base, make_join_table

provider_degree_table = make_join_table("provider", "degree")


class Degree(Base):
    acronym = Column(String(16), unique=True, nullable=False)
    name = Column(String(), nullable=False)
    level = Column(Enum(EducationLevel), nullable=False)

    providers = relationship("Provider", secondary=provider_degree_table,
                             back_populates="degrees")


UniqueConstraint(Degree.acronym, Degree.name)
UniqueConstraint(Degree.acronym, Degree.level)
