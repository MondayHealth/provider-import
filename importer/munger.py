import configparser
from typing import Mapping, Type, Iterable, List

import progressbar
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session, load_only

from db_url import get_db_url
from importer.fixture_updater import FixtureUpdater
from importer.loader import RawTable
from importer.munger_plugin_base import MungerPlugin
from importer.util import mutate, m
from provider.models.directories import Directory
from provider.models.license import License
from provider.models.licensor import Licensor
from provider.models.payors import Payor
from provider.models.plans import Plan
from provider.models.providers import Provider

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

    NYSOP_NAME = "New York State Office of the Professions"

    ROW_FIELDS = {
        'source_updated_at': str,
        'created_at': str,
        'updated_at': str,
        'first_name': str,
        'last_name': str,
        'maximum_fee': int,
        'minimum_fee': int,
        'sliding_scale': bool,
        'free_consultation': bool,
        'website_url': str,
        'accepting_new_patients': bool,
        'began_practice': int,
        'school': str,
        'year_graduated': int,
    }

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

    def __init__(self, plugins: Iterable[Type[MungerPlugin]], debug: bool):
        config = configparser.ConfigParser()
        config.read("alembic.ini")
        url = get_db_url()
        print("Creating engine at", url)
        self._engine = create_engine(url, echo=ECHO_SQL)
        session_factory = sessionmaker(bind=self._engine)
        self._Session = scoped_session(session_factory)
        self._Session.configure()
        self._session: Session = self._Session()
        self._load_nysop()

        # init plugins with session
        self._plugins: List[MungerPlugin] = []
        for constructor in plugins:
            self._plugins.append(constructor(self._session, debug))

    def _load_nysop(self):
        # Construct the NYS OP licensor
        nysop = self._session.query(Licensor).filter_by(
            name=self.NYSOP_NAME).one_or_none()

        if not nysop:
            print("Constructing", self.NYSOP_NAME)
            nysop = Licensor(name=self.NYSOP_NAME, state="NY")
            self._session.add(nysop)

        self._nysop: Licensor = nysop

    def update_fixtures(self) -> None:
        fu = FixtureUpdater(self._session)
        fu.run()
        self._session.commit()

    def load_small_tables(self, tables: Mapping[str, RawTable]) -> None:
        self._directories(tables['directories'])
        self._payors(tables['payors'])
        self._plans(tables['plans'])
        self._session.commit()

    def process_providers(self, tables: Mapping[str, RawTable],
                          update_columns: bool) -> None:

        for plugin in self._plugins:
            plugin.pre_process()

        table = tables['provider_records']
        columns, rows = table.get_table_components()

        name_modified: bool = False

        i = 0
        bar = progressbar.ProgressBar(max_value=len(rows), initial_value=i)
        for row in rows:
            row_id = m(row, 'id', int)
            license_number = m(row, 'license_number', str)

            # Try to find a license number
            lic = None
            if license_number:
                q = self._session.query(License).filter_by(
                    number=license_number, licensor_id=self._nysop.id)
                lic = q.options(load_only("licensee_id")).one_or_none()
                if lic:
                    row_id = lic.licensee_id

            # Does this provider exist?
            provider: Provider = self._session.query(Provider).filter_by(
                id=row_id).options(load_only("id")).one_or_none()

            if not provider or update_columns:
                name_modified = True
                args = {}
                for k, v in self.ROW_FIELDS.items():
                    val = m(row, k, v)
                    # This check is important because we want fields that are
                    # set to null to not overwrite existing fields from other
                    # record sources
                    if val is not None:
                        args[k] = val
                provider: Provider = Provider(id=row_id, **args)
                provider = self._session.merge(provider)

            # Add the nysop license if its not there
            if not lic and license_number:
                lic = License(number=license_number, licensee=provider,
                              licensor=self._nysop)
                """
                It's a requirement of association tables in sqlalchemy that the
                "child" in the relationship must be explicitly associated with
                the association record. see:
                docs.sqlalchemy.org/en/latest/orm/basic_relationships.html
                #association-object
                """
                provider.licenses.append(lic)

            # Do all the plugins
            for plugin in self._plugins:
                plugin.process_row(row, provider)

            self._session.commit()
            i += 1
            bar.update(i)

        self._session.flush()

        for plugin in self._plugins:
            plugin.post_process()

    def _update_tsv(self, table: str, field: str = "tsv",
                    content: str = "body") -> None:
        print("Updating", table, "tsv...")
        self._session.execute(
            "UPDATE monday.{} SET {} = to_tsvector('english', {});".format(
                table, field, content))
        print("Done.")

    def clean(self) -> None:

        print()
        self._update_tsv("provider", "name_tsv", """
        coalesce(first_name,'') || ' ' || coalesce(middle_name,'') || ' ' 
            || coalesce(last_name,'')
        """)
        self._update_tsv("orientation")
        self._update_tsv("group")
        self._update_tsv("acceptedpayorcomment")
        self._update_tsv("address", "formatted_tsv", "formatted")

        # Clean up
        print("Calling VACUUM FULL VERBOSE ANALYSE ...")
        connection = self._engine.raw_connection()
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        cursor.execute("VACUUM FULL VERBOSE ANALYSE;")
        print("Done.")
