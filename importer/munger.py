import configparser
import datetime
from typing import Mapping, Type, Iterable, List, MutableMapping, Set, Union

# This import is fucked up but i like pbar
# noinspection PyPackageRequirements
import progressbar
from redis import StrictRedis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from db_url import get_db_url
from dedupe.deduplicator import ROW_ID_HASH
from importer.fixture_updater import FixtureUpdater
from importer.loader import RawTable
from importer.munger_plugin_base import MungerPlugin
from importer.util import mutate, m
from provider.models.directories import Directory
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

    # 3 == good therapy, 4 == pn
    ROW_FIELDS = {
        'source_updated_at': (str, None),
        'created_at': (str, None),
        'updated_at': (str, None),
        'first_name': (str, (4, 3)),
        'last_name': (str, None),
        'maximum_fee': (int, (4,)),
        'minimum_fee': (int, (4,)),
        'sliding_scale': (bool, (4,)),
        'free_consultation': (bool, (3,)),
        'website_url': (str, (4,)),
        'accepting_new_patients': (bool, None),
        'school': (str, None),
        'year_graduated': (int, None),
    }

    def _directories(self, table: RawTable) -> None:
        columns, rows = table.get_table_components()
        i = 0
        bar = progressbar.ProgressBar(max_value=len(rows))
        for row in rows:
            mutate(row, 'record_limit', int)
            directory = self._session.merge(Directory(**row))
            self._directory_map[directory.id] = directory
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

        assert "id" not in self.ROW_FIELDS, "Should not set ID!"

        config = configparser.ConfigParser()
        config.read("alembic.ini")
        url = get_db_url()
        print("Creating engine at", url)
        self._engine = create_engine(url, echo=ECHO_SQL)
        session_factory = sessionmaker(bind=self._engine)
        self._Session = scoped_session(session_factory)
        self._Session.configure()
        self._session: Session = self._Session()
        self._r = StrictRedis(decode_responses=True)

        self._directory_map: MutableMapping[int, Directory] = {}

        # init plugins with session
        self._plugins: List[MungerPlugin] = []
        for constructor in plugins:
            self._plugins.append(constructor(self._session, debug))

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

        directories: MutableMapping[int, Set[int]] = {}

        current_year: int = datetime.datetime.now().year

        i = 0
        bar = progressbar.ProgressBar(max_value=len(rows), initial_value=i)
        for row in rows:

            row_id = m(row, 'id', int)

            assert row_id, "there must be a row id"

            directory_id: Union[int, None] = m(row, 'directory_id', int)

            canonical_id: int = int(self._r.hget(ROW_ID_HASH, row_id))

            # Does this provider exist?
            provider: Provider = self._session.query(Provider).filter_by(
                id=canonical_id).one_or_none()

            if not provider or update_columns:
                dirs: Union[int, None] = directories.get(canonical_id, None)
                args = {}

                for row_name, row_params in self.ROW_FIELDS.items():
                    coercer, priorities = row_params

                    # @TODO: NOTE!! If a higher priority row had no value, lower
                    # @TODO: priority rows WITH values will skip!! I am highly
                    # @TODO: suspicious that this will work for all cases!!
                    if dirs:
                        skip = False
                        for priority in priorities:
                            # Are we this priority?
                            if directory_id == priority:
                                break
                            # Do we already have a higher priority?
                            if priority in dirs:
                                skip = True
                                continue
                        if skip:
                            continue

                    # Get the value
                    coerced_value = m(row, row_name, coercer)

                    # This check is important because we want fields that are
                    # set to null to not overwrite existing fields from other
                    # record sources
                    if coerced_value is not None:
                        args[row_name] = coerced_value

                # Regardless of the outcome, we can still merge a new record
                args['id'] = canonical_id
                provider: Provider = Provider(**args)
                provider = self._session.merge(provider)

                # A special case
                yip: int = m(row, 'years_in_practice', int)
                if not yip or yip < 1:
                    provider.began_practice = current_year - yip

            # Relate the provider to the directory
            if directory_id and directory_id in self._directory_map:
                provider.directories.append(self._directory_map[directory_id])

            # Do all the plugins
            for plugin in self._plugins:
                plugin.process_row(row, provider)

            # Save the directories processed for this canonical ID so that when
            # we find another one we can evaluate priority
            if canonical_id not in directories:
                directories[canonical_id] = {directory_id}
            else:
                directories[canonical_id].add(directory_id)

            self._session.commit()
            i += 1
            bar.update(i)

        self._session.flush()

        for plugin in self._plugins:
            plugin.post_process()
