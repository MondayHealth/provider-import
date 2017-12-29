import configparser
from typing import Mapping

import progressbar
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from db_url import get_db_url
from importer.loader import RawTable
from importer.provider_munger import ProviderMunger
from importer.util import mutate
from provider.models.directories import Directory
from provider.models.payors import Payor
from provider.models.plans import Plan

ECHO_SQL = False


def _directories(table: RawTable, session: Session) -> None:
    columns, rows = table.get_table_components()
    i = 0
    bar = progressbar.ProgressBar(max_value=len(rows))
    for row in rows:
        mutate(row, 'record_limit', int)
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
        mutate(row, 'record_limit', int)
        mutate(row, 'original_code', str)
        session.merge(Plan(**row))
        bar.update(i)
        i = i + 1


class Munger:
    """ Take a bunch of raw tables and create a bulk insertion """

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("alembic.ini")
        url = get_db_url()
        print("Creating engine at", url)
        self._engine = create_engine(url, echo=ECHO_SQL)
        session_factory = sessionmaker(bind=self._engine)
        self._Session = scoped_session(session_factory)
        self._Session.configure()

    def munge(self, tables: Mapping[str, RawTable]) -> None:
        session: Session = self._Session()
        _directories(tables['directories'], session)
        _payors(tables['payors'], session)
        _plans(tables['plans'], session)
        session.commit()

        pm = ProviderMunger(session)
        failed = pm.load_table(tables['provider_records'])
        session.commit()

        session.close()

        # Clean up
        print()
        print("Calling ANALYZE...")
        self._engine.execute("ANALYZE;")
        print("Done.")

        print("Failed:")
        for row in failed:
            print(row)
