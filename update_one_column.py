""" Use this script to update a single column for every provider """

import datetime

import progressbar
from redis import StrictRedis
from sqlalchemy import text
from sqlalchemy.orm import Session

from dedupe.deduplicator import ROW_ID_HASH
from importer.loader import CSVLoader
from importer.npi_import import NPIImporter
from importer.util import m


class SingleColumnUpdater:
    def __init__(self):
        self._session: Session = NPIImporter.get_session()
        self._r: StrictRedis = StrictRedis(decode_responses=True)

    def run(self) -> None:
        base_path: str = '/Users/ixtli/Downloads/monday'
        loader: CSVLoader = CSVLoader(base_path)
        loader.load()
        tables = loader.get_tables()
        table = tables['provider_records']
        columns, rows = table.get_table_components()

        query: text = text("""
        UPDATE monday.provider SET began_practice = :val WHERE id = :id
        """)

        current_year: int = datetime.datetime.now().year

        params: dict = {'val': None, 'id': None}

        updated = 0
        i = 0
        bar = progressbar.ProgressBar(max_value=len(rows), initial_value=i)
        for row in rows:
            yip: int = m(row, 'years_in_practice', int)
            if not yip or yip < 1:
                i += 1
                bar.update(i)
                continue

            row_id = m(row, 'id', int)
            assert row_id, "there must be a row id"

            canonical_id: int = int(self._r.hget(ROW_ID_HASH, row_id))

            params['val'] = current_year - yip
            params['id'] = canonical_id

            self._session.execute(query, params)

            updated += 1

            if updated % 250:
                self._session.commit()

            i += 1
            bar.update(i)

        self._session.commit()

        print()
        print("Updated", updated, "rows.")


if __name__ == "__main__":
    SingleColumnUpdater().run()
