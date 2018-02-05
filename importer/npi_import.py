import configparser
import json
from typing import List, MutableMapping

import progressbar
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session, load_only

from db_url import get_db_url
from provider.models.address import Address
from provider.models.directories import Directory
from provider.models.license import License
# noinspection PyUnresolvedReferences
from provider.models.providers import Provider


class NPIImporter:
    PATH = "/Users/ixtli/Downloads/monday/NY.json"

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

        directory = self._session.query(Directory).filter_by(
            short_name="npi").one_or_none()

        if not directory:
            print("Creating NPI Directory Entry.")
            directory = Directory(short_name="npi",
                                  name="National Provider Identifier")
            self._session.add(directory)
            self._session.commit()

        print("Directory ID", directory.id)
        self._directory: Directory = directory

    def load(self) -> None:
        print("Loading NPI distilate at", self.PATH, "...")
        with open(self.PATH) as f:
            self.raw = json.load(f)
        print("Done")

    def add_practice_locations(self) -> None:
        # noinspection PyUnresolvedReferences
        directory_id: int = self._directory.id
        query_base = self._session.query(Address)
        idx = 0
        added = 1
        bar = progressbar.ProgressBar(initial_value=0, max_value=len(self.raw))
        for element in self.raw:
            addrs: MutableMapping[str, dict] = element['addresses']
            for address_type, address in addrs.items():
                first: str = address.get("first_line").strip()
                state: str = address.get("state")
                zip_code: str = address.get("zip", "").replace("-", "").strip()

                assert zip_code, "No zip code!"
                assert first, "No first line!"
                assert state, "No state!"

                plus_four: str = ""
                if len(zip_code) > 5:
                    plus_four = zip_code[5:]
                    zip_code = zip_code[:5]

                components = [
                    first.title(),
                    address.get("second_line", "").title(),
                    zip_code,
                    state.upper(),
                ]

                raw = ""
                for component in components:
                    if not component:
                        continue
                    raw += " " + component.strip()

                country: str = address.get("country")
                if country != "US":
                    raw += " " + country

                if not query_base.filter_by(raw=raw).one_or_none():
                    new_address = Address(raw=raw, directory_id=directory_id)
                    self._session.add(new_address)
                    added += 1

            idx += 1
            bar.update(idx)

            if idx % 1000:
                self._session.commit()

        self._session.commit()
        print("Added", added, "new addresses.")

    def dedupe(self) -> None:
        bar = progressbar.ProgressBar(initial_value=0, max_value=len(self.raw))
        idx = 0
        matched = 0

        q = self._session.query(License).options(
            load_only("number", "licensee_id"))
        print("Loading all licenses...")
        nys_license_map: MutableMapping[str, int] = {}
        existing: List[License] = q.all()
        for record in existing:
            number = record.number
            if number[0] == "R":
                number = number[1:]
            if number[-2:] == "-1":
                number = number[:-2]
            nys_license_map[number] = record.licensee_id
        print("Done:", len(nys_license_map))

        for element in self.raw:
            names = element['names']
            credentials = element['credentials']
            phones = element['phones']
            addresses = element['addresses']
            licenses = element['licenses']

            c_id = None

            for license_num in licenses.keys():
                number = license_num
                if number[0] == "R":
                    number = number[1:]
                if number[-2:] == "-1":
                    number = number[:-2]
                if number in nys_license_map:
                    matched += 1
                    c_id = nys_license_map[number]

            # Update matched records with NPI number, gender, phones, practice
            # Add un-matched records with basic information.

            idx += 1
            bar.update(idx)

        print()
        print("matched", matched, "by exact license")


def _run_from_cli():
    n = NPIImporter()
    n.load()
    # n.dedupe()
    n.add_practice_locations()


if __name__ == "__main__":
    _run_from_cli()
