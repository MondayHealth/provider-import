import configparser
import re
from collections import OrderedDict
from typing import Mapping, Union

import progressbar
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from importer.loader import RawTable
from provider.models.address import Address
from provider.models.directories import Directory
from provider.models.payors import Payor
from provider.models.plans import Plan
from provider.models.providers import Provider


def int_or_none(row: OrderedDict, name: str) -> None:
    v = row[name]
    if not v:
        row[name] = None
    else:
        row[name] = int(v)


def str_or_none(row: OrderedDict, name: str) -> None:
    v = row[name]
    if not v:
        row[name] = None
    else:
        row[name] = str(v)


def de_camel(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def parse_locations(raw: str, session: Session) -> Union[Address, None]:


def _provider(table: RawTable, session: Session) -> None:
    columns, rows = table.get_table_components()
    i = 0
    bar = progressbar.ProgressBar(max_value=len(rows))
    for row in rows:
        raw = row['address'].strip()
        address = session.merge(Address(raw=raw))

        row['address'] = address

        provider = Provider(**row)
        bar.update(i)
        i = i + 1


def _directories(table: RawTable, session: Session) -> None:
    columns, rows = table.get_table_components()
    i = 0
    bar = progressbar.ProgressBar(max_value=len(rows))
    for row in rows:
        int_or_none(row, 'record_limit')
        session.merge(Directory(**row))
        bar.update(i)
        i = i + 1


def _payors(table: RawTable, session: Session) -> None:
    columns, rows = table.get_table_components()
    i = 0
    bar = progressbar.ProgressBar(max_value=len(rows))
    for row in rows:
        session.merge(Payor(**row))
        bar.update(i)
        i = i + 1


def _plans(table: RawTable, session: Session) -> None:
    columns, rows = table.get_table_components()
    i = 0
    bar = progressbar.ProgressBar(max_value=len(rows))
    for row in rows:
        int_or_none(row, 'record_limit')
        str_or_none(row, 'original_code')
        session.merge(Plan(**row))
        bar.update(i)
        i = i + 1


class Munger:
    """ Take a bunch of raw tables and create a bulk insertion """

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("alembic.ini")
        url = config['alembic']['sqlalchemy.url']
        print("Creating engine at", url)
        self._engine = create_engine(url, echo=True)
        session_factory = sessionmaker(bind=self._engine)
        self._Session = scoped_session(session_factory)

    def munge(self, tables: Mapping[str, RawTable]) -> None:
        # _locations(tables['locations'])
        session: Session = self._Session()
        _directories(tables['directories'], session)
        _payors(tables['payors'], session)
        _plans(tables['plans'], session)
        session.commit()
        session.close()

        # Clean up
        print()
        print("Calling ANALYZE...")
        self._engine.execute("ANALYZE;")
        print("Done.")
