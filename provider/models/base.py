import datetime
from typing import Union, List

from sqlalchemy import Column, Integer, DateTime, Table, ForeignKey, \
    UniqueConstraint
from sqlalchemy.ext.declarative import declared_attr, declarative_base


class BaseBase:
    """
    The class from which the declarative_base will be instantiated. It should
    contain fields and settings that will apply to ALL tables. Otherwise make
    another mixin
    """

    id = Column(Integer, primary_key=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow,
                        nullable=False)

    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        nullable=False, onupdate=datetime.datetime.utcnow)

    @declared_attr
    def __tablename__(self) -> str:
        return self.__name__.lower()

    @declared_attr
    def __table_args__(self) -> dict:
        return {'schema': 'monday'}


Base = declarative_base(cls=BaseBase)
Base.metadata.schema = "monday"


def _pluralize(word: str) -> str:
    ret = word + "s"
    if word[-1] == "y":
        ret = word[:-1] + "ies"
    if word[-2:] == "ss":
        ret = word + "es"
    # print("plural of", word, "is", ret)
    return ret


def make_join_table(left_in: str, right_in: str, unique: bool = True) -> Table:
    left = left_in.lower()
    right = right_in.lower()
    left_plural = _pluralize(left)
    right_plural = _pluralize(right)

    left_column_name = left + "_id"
    right_column_name = right + "_id"
    table_name = "{}_{}".format(left_plural, right_plural)

    params: List[Union[Column, UniqueConstraint]] = [
        Column(left_column_name, Integer, ForeignKey(left + ".id")),
        Column(right_column_name, Integer, ForeignKey(right + ".id"))
    ]

    if unique:
        params += [UniqueConstraint(left_column_name, right_column_name)]

    return Table(table_name, Base.metadata, *params)
