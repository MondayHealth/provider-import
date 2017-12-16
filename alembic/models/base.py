from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declared_attr, declarative_base


class BaseBase:
    """
    The class from which the declarative_base will be instantiated. It should
    contain fields and settings that will apply to ALL tables. Otherwise make
    another mixin
    """

    id = Column(Integer, primary_key=True)

    #
    created_at = Column(DateTime, nullable=False)

    #
    updated_at = Column(DateTime, nullable=False)

    @declared_attr
    def __tablename__(self) -> str:
        return self.__name__.lower()


Base = declarative_base(cls=BaseBase)
Base.metadata.schema = "provider"
