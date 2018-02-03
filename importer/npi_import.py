import configparser
import json
from typing import List, MutableMapping

import progressbar
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session, load_only

from db_url import get_db_url
from provider.models.license import License
# noinspection PyUnresolvedReferences
from provider.models.providers import Provider


class NPIImporter:
    PATH = "/Users/ixtli/Public/project/py/npi-db-tools/NY.json"

    def __init__(self):
        self.raw: List[dict] = []
        config = configparser.ConfigParser()
        config.read("alembic.ini")
        url = get_db_url()
        print("Creating engine at", url)
        engine = create_engine(url)
        session_factory = sessionmaker(bind=engine)
        session = scoped_session(session_factory)
        session.configure()
        self._session: Session = session()

    def load(self) -> None:
        print("Loading NPI distilate at", self.PATH, "...")
        with open(self.PATH) as f:
            self.raw = json.load(f)
        print("Done")

    def dedupe(self) -> None:
        bar = progressbar.ProgressBar(initial_value=0, max_value=len(self.raw))
        idx = 0
        matched = 0

        q = self._session.query(License).options(
            load_only("number", "licensee_id"))
        print("Loading all licenses...")
        m: MutableMapping[str, int] = {}
        existing: List[License] = q.all()
        for record in existing:
            m[record.number] = record.licensee_id
        print("Done:", len(m))

        for element in self.raw:
            names = element['names']
            credentials = element['credentials']
            phones = element['phones']
            addresses = element['addresses']
            licenses = element['licenses']

            for license_num in licenses.keys():
                if license_num in m:
                    matched += 1

            idx += 1
            bar.update(idx)

        print("matched", matched, "by exact license")


def _run_from_cli():
    n = NPIImporter()
    n.load()
    n.dedupe()


if __name__ == "__main__":
    _run_from_cli()
