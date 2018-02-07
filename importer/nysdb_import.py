import pprint
from typing import List, Union, Set, MutableMapping

import progressbar
from sqlalchemy import text
from sqlalchemy.engine import ResultProxy
from sqlalchemy.orm import Session

from importer.license_cert_munger import LicenseCertMunger
from importer.npi_import import NPIImporter
from provider.models.address import Address
# noinspection PyUnresolvedReferences
from provider.models.directories import Directory
from provider.models.license import License
from provider.models.licensor import Licensor


class RawLine:
    @staticmethod
    def _int_or_none(raw: str, start: int, end: int) -> Union[int, None]:
        value = raw[start:end].strip()
        if value:
            return int(value)
        else:
            return None

    def __init__(self, raw: str) -> None:
        self.profession_code: int = int(raw[:2])
        self.registration_status: str = raw[2:3]
        self.license_number: int = int(raw[3:9])
        self.names: List[str] = raw[9:45].strip().split(" ")
        self.address: List[str] = [
            raw[45:66].strip().title(),
            raw[66:87].strip().title(),
            raw[87:108].strip().title(),
        ]
        self.city: str = raw[108:127].strip().title()
        self.state: str = raw[127:129]
        self.zip: Union[int, None] = self._int_or_none(raw, 129, 134)
        self.zip_plus_four: Union[int, None] = self._int_or_none(raw, 134, 138)
        self.county_code: str = raw[138:140]
        self.regents_action: bool = raw[141] == "*"
        self.license_date: str = raw[141:168]
        self.registration_ending_date: str = raw[168:172]
        self.child_abuse_code: str = raw[173]
        self.infectious_disease_code: str = raw[174]
        self.degree_date: str = raw[174:182]
        self.school: str = raw[182:207]
        self.email: str = raw[207:247]
        self.phone: str = raw[247:].strip()

    def get_address(self) -> str:
        components = self.address + [self.city, self.state]
        if self.zip:
            components.append(str(self.zip))
        return " ".join(components)


class NYSDBImporter:
    PATH: str = "/Users/ixtli/Downloads/monday/nysdb.txt"

    FULL_NAME: str = "New York Office of Professions"

    def __init__(self) -> None:
        self._session: Session = NPIImporter.get_session()

        self._rows: List[RawLine] = []
        self._directory: Directory = self._get_directory()
        self._licensor: Licensor = LicenseCertMunger.get_or_create_nysop(
            self._session)

    def _get_directory(self) -> Directory:
        directory = self._session.query(Directory).filter_by(
            short_name="nysop").one_or_none()

        if not directory:
            print("Creating NYSOP Directory Entry.")
            directory = Directory(short_name="nysop",
                                  name=LicenseCertMunger.NYSOP_NAME)
            self._session.add(directory)
            self._session.commit()

        # noinspection PyUnresolvedReferences
        print("Directory ID", directory.id)
        return directory

    def load(self) -> None:
        print("Reading", self.PATH)
        with open(self.PATH, 'r', errors='replace') as f:
            lines: List[str] = f.readlines()
        print("Done.")

        bar = progressbar.ProgressBar(initial_value=0, max_value=len(lines))
        idx = 0
        for line in lines:
            self._rows.append(RawLine(line))
            idx += 1
            bar.update(idx)

    def dedupe_and_update(self) -> None:
        count = len(self._rows)
        bar = progressbar.ProgressBar(initial_value=0, max_value=count)
        idx = 0
        added = []
        updated = []
        conflict = []

        provider_x_name = text("""
        SELECT id, first_name, last_name
        FROM monday.provider
        WHERE name_tsv @@ :tsq :: TSQUERY
        """)

        license_q = text("""
        SELECT licensee_id, secondary_number
        FROM monday.license
        WHERE number = :license
        """)

        for row in self._rows:
            idx += 1
            bar.update(idx)

            # @TODO: Maybe check: last_name LIKE "%names[0].title()%"  ???

            # Is VERY similar to the full name
            result: ResultProxy = self._session.execute(provider_x_name, {
                "tsq": " & ".join(row.names)
            })

            # @TODO: Maybe a TSQUERY for just the last name?

            found: MutableMapping[int] = set()
            for record in result.fetchall():
                found[record.id] = record.first_name + record.last_name

            result = self._session.execute(license_q, {
                "license": str(row.license_number).zfill(6)
            })

            for record in result.fetchall():
                if record.licensee_id in found:
                    if record.secondary_number == row.profession_code:
                        # This record is almost 100% the same


            if idx % 1000:
                self._session.commit()

        self._session.commit()

    def add_new_addresses(self) -> None:
        count = len(self._rows)
        bar = progressbar.ProgressBar(initial_value=0, max_value=count)
        idx = 0
        added = 0
        # noinspection PyUnresolvedReferences
        did: int = self._directory.id
        for row in self._rows:
            idx += 1
            bar.update(idx)
            # Pointlessly inaccurate
            if not "".join(row.address).strip():
                continue

            q = self._session.query(Address).filter_by(raw=row.get_address())

            address: Address = q.one_or_none()

            if not address:
                address = Address(raw=row.get_address(), directory_id=did)
                if row.zip:
                    address.zip_code = row.zip
                self._session.add(address)
                added += 1
            else:
                if not address.directory_id:
                    address.directory_id = did

            if idx % 1000:
                self._session.commit()

        self._session.commit()

        print("Added", added, "records out of", count, "total.")

    def test_munger(self) -> None:
        """ This might not have a reason to be in this file but its a good
        scaffold to test the nysop cleaner """
        licenses: List[License] = self._session.query(License).all()
        count = len(licenses)
        bar = progressbar.ProgressBar(initial_value=0, max_value=count)
        idx = 0
        not_nysop = set()
        results = []
        prof_codes = set()
        # noinspection PyUnresolvedReferences
        for lic in licenses:
            idx += 1
            bar.update(idx)
            raw: str = lic.number
            clean, code, nysop = LicenseCertMunger.clean_up_nysop_number(raw)
            if not nysop:
                not_nysop.add(raw)
            else:
                prof_codes.add(code)
                results.append((raw, clean, code))

        print("Not NYSOP:")
        pprint.pprint(not_nysop)
        print("Professional Codes:")
        pprint.pprint(prof_codes)
        print("NYSOP")
        for raw, clean, code in results:
            if len(raw) > 6:
                print(clean, code, raw)


def _run_from_cli():
    n = NYSDBImporter()
    # n.load()
    # n.add_new_addresses()
    n.test_munger()


if __name__ == "__main__":
    _run_from_cli()
