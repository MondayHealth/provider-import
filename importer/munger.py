import configparser
import re
from typing import Mapping

import progressbar
import usaddress
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from importer.loader import RawTable
from provider.models.directories import Directory
from provider.models.payors import Payor
from provider.models.plans import Plan


def de_camel(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _locations(table: RawTable) -> None:
    parts = {}
    types = {}
    failures = []
    columns, rows = table.get_table_components()
    i = 0
    bar = progressbar.ProgressBar(max_value=len(rows))
    for row in rows:
        try:
            tag, address_type = usaddress.tag(row["address"])
        except usaddress.RepeatedLabelError as e:
            failures.append((row, e.MESSAGE))
            continue

        if address_type not in types:
            types[address_type] = 0
        else:
            types[address_type] = types[address_type] + 1

        for key, val in tag.items():
            dc_key = de_camel(key)
            if dc_key not in parts:
                parts[dc_key] = len(val)
            else:
                parts[dc_key] = max(len(val), parts[dc_key])

        bar.update(i)
        i = i + 1

    print()
    print("address types:", types)
    print("failed to parse", len(failures), "addresses")


def _directories(table: RawTable, session: Session) -> None:
    columns, rows = table.get_table_components()
    i = 0
    bar = progressbar.ProgressBar(max_value=len(rows))
    for row in rows:
        directory = Directory(**row)
        session.add(directory)
        bar.update(i)
        i = i + 1


def _payors(table: RawTable, session: Session) -> None:
    columns, rows = table.get_table_components()
    print(columns)
    i = 0
    bar = progressbar.ProgressBar(max_value=len(rows))
    for row in rows:
        payor = Payor(**row)
        session.add(payor)
        bar.update(i)
        i = i + 1


def _plans(table: RawTable, session: Session) -> None:
    columns, rows = table.get_table_components()
    i = 0
    bar = progressbar.ProgressBar(max_value=len(rows))
    for row in rows:
        plan = Plan(**row)
        session.add(plan)
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
        #_payors(tables['payors'], session)
        #_plans(tables['plans'], session)
        session.commit()
        session.close()
