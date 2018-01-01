import configparser
from typing import Mapping

import progressbar
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from db_url import get_db_url
from importer.credentials_munger import CredentialsMunger
from importer.fixture_updater import FixtureUpdater
from importer.loader import RawTable
from importer.provider_munger import ProviderMunger
from importer.util import mutate
from provider.models.directories import Directory
from provider.models.payors import Payor
from provider.models.plans import Plan

ECHO_SQL = False


def labeled_bar(name: str) -> progressbar.ProgressBar:
    widgets = [
        name, " ",
        progressbar.RotatingMarker(), " ",
        progressbar.Counter(), " ",
        progressbar.Timer()
    ]
    return progressbar.ProgressBar(max_value=progressbar.UnknownLength,
                                   widgets=widgets)


class Munger:
    """ Take a bunch of raw tables and create a bulk insertion """

    def _directories(self, table: RawTable) -> None:
        columns, rows = table.get_table_components()
        i = 0
        bar = progressbar.ProgressBar(max_value=len(rows))
        for row in rows:
            mutate(row, 'record_limit', int)
            self._session.merge(Directory(**row))
            bar.update(i)
            i = i + 1

    def _payors(self, table: RawTable) -> None:
        columns, rows = table.get_table_components()
        i = 0
        bar = progressbar.ProgressBar(max_value=len(rows))
        for row in rows:
            self._session.merge(Payor(**row))
            bar.update(i)
            i = i + 1

    def _plans(self, table: RawTable) -> None:
        columns, rows = table.get_table_components()
        i = 0
        bar = progressbar.ProgressBar(max_value=len(rows))
        for row in rows:
            mutate(row, 'record_limit', int)
            mutate(row, 'original_code', str)
            self._session.merge(Plan(**row))
            bar.update(i)
            i = i + 1

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("alembic.ini")
        url = get_db_url()
        print("Creating engine at", url)
        self._engine = create_engine(url, echo=ECHO_SQL)
        session_factory = sessionmaker(bind=self._engine)
        self._Session = scoped_session(session_factory)
        self._Session.configure()
        self._session: Session = self._Session()

    def update_fixtures(self) -> None:
        fu = FixtureUpdater(self._session)
        fu.run()
        self._session.commit()

    def load_providers(self, tables: Mapping[str, RawTable]) -> None:
        self._directories(tables['directories'])
        self._payors(tables['payors'])
        self._plans(tables['plans'])
        self._session.commit()

        pm = ProviderMunger(self._session)
        failed = pm.load_table(tables['provider_records'])
        self._session.commit()

        print("Failed:")
        for row in failed:
            print(row)

    def process_credentials_in_place(self, t: Mapping[str, RawTable]) -> None:
        ipcp = CredentialsMunger(self._session)
        ipcp.process(t['provider_records'])
        self._session.commit()
        ipcp.print_skipped()

    def clean(self) -> None:
        # Clean up
        print()
        print("Calling ANALYZE...")
        self._engine.execute("ANALYZE;")
        print("Done.")
