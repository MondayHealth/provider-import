from sqlalchemy import Column, Integer, DateTime, Table, ForeignKey
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


def make_join_table(left: str, right: str) -> Table:
    left_plural = left
    right_plural = right

    if left_plural[-1] == "y":
        left_plural = left_plural[:-1] + "ies"

    if right_plural[-1] == "y":
        right_plural = right_plural[:-1] + "ies"

    return Table("{}s_{}s".format(left_plural, right_plural),
                 Base.metadata,
                 Column(left + "_id", Integer, ForeignKey(left + ".id")),
                 Column(right + "_id", Integer, ForeignKey(right + ".id")))
