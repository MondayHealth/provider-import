import configparser
import json
from typing import List, MutableMapping, Mapping, Set

import progressbar
from sqlalchemy import create_engine, text
from sqlalchemy.engine import ResultProxy
from sqlalchemy.orm import sessionmaker, scoped_session, Session, load_only

from db_url import get_db_url
from importer.credential_parser import CredentialParser
from importer.license_cert_munger import LicenseCertMunger
from importer.phone_addy_munger import PhoneAddyMunger
from provider.models.address import Address
from provider.models.credential import Credential
from provider.models.degree import Degree
from provider.models.directories import Directory
from provider.models.licensor import Licensor
from provider.models.phones import Phone
from provider.models.providers import Provider


class NPIImporter:
    PATH: str = "/Users/ixtli/Downloads/monday/NY.json"

    NPI_FULL_NAME: str = "National Provider Identifier Standard"

    def __init__(self):
        self.raw: Mapping[int, dict] = {}
        self.nys_license_map: MutableMapping[str, MutableMapping[str, int]] = {}
        self._degree_map: MutableMapping[str, Degree] = {}
        self._credential_map: MutableMapping[str, Credential] = {}
        self._npi_map: MutableMapping[int, int] = {}
        self._session: Session = self.get_session()
        self._directory: Directory = self._get_directory()
        self._licensor: Licensor = self._get_licensor()

    @staticmethod
    def get_session() -> Session:
        config = configparser.ConfigParser()
        config.read("alembic.ini")
        url = get_db_url()
        print("Creating engine at", url)
        engine = create_engine(url)
        session_factory = sessionmaker(bind=engine)
        session = scoped_session(session_factory)
        session.configure()
        return session()

    def _get_directory(self) -> Directory:
        directory = self._session.query(Directory).filter_by(
            short_name="npi").one_or_none()
        if not directory:
            print("Creating NPI Directory Entry.")
            directory = Directory(short_name="npi",
                                  name="National Provider Identifier")
            self._session.add(directory)
            self._session.commit()

        # noinspection PyUnresolvedReferences
        print("Directory ID", directory.id)
        return directory

    def _get_licensor(self) -> Licensor:
        # Construct the NYS OP licensor
        npi: Licensor = self._session.query(Licensor).filter_by(
            name=self.NPI_FULL_NAME).one_or_none()

        if not npi:
            print("Constructing", self.NPI_FULL_NAME)
            npi = Licensor(name=self.NPI_FULL_NAME)
            self._session.add(npi)

        return npi

    def load(self) -> Set[str]:
        print("Loading NPI distilate at", self.PATH, "...")
        with open(self.PATH) as f:
            self.raw = json.load(f)
        print("Done")

        print("Getting all credentials...")
        q = self._session.query(Credential).options(
            load_only("id", "acronym"))
        credentials: List[Credential] = q.all()
        for credential in credentials:
            # noinspection PyUnresolvedReferences
            self._credential_map[credential.acronym.lower()] = credential
        print("Done.")

        print("Getting all degrees...")
        q = self._session.query(Degree).options(load_only("id", "acronym"))
        degrees: List[Degree] = q.all()
        for degree in degrees:
            # noinspection PyUnresolvedReferences
            self._degree_map[degree.acronym.lower()] = degree
        print("Done.")

        q = text("""
        SELECT prov.last_name, prov.first_name, number, licensee_id
        FROM monday.license
          JOIN monday.provider AS prov ON licensee_id = prov.id
        WHERE licensor_id = 1
        """)

        ambigous: Set[str] = set()
        print("Loading all licenses...")
        for record in self._session.execute(q).fetchall():
            number = record.number

            last_name = record.last_name.strip().lower()

            if last_name in ambigous:
                continue

            lid = record.licensee_id

            if number not in self.nys_license_map:
                self.nys_license_map[number] = {}

            if last_name in self.nys_license_map[number]:
                if self.nys_license_map[number][last_name] != lid:
                    ambigous.add(last_name)
                    del self.nys_license_map[number][last_name]
                    continue

            self.nys_license_map[number][last_name] = lid

        print("Done.")

        # lol
        for ambiguo in ambigous:
            print(ambiguo)

        print()

        return ambigous

    @staticmethod
    def _address_to_raw(address: dict) -> str:
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

        return raw

    def add_practice_locations(self) -> None:
        # noinspection PyUnresolvedReferences
        directory_id: int = self._directory.id
        query_base = self._session.query(Address)
        idx = 0
        added = 1
        bar = progressbar.ProgressBar(initial_value=0, max_value=len(self.raw))
        for npi, element in self.raw.items():
            addresses: MutableMapping[str, dict] = element['addresses']
            for address_type, address in addresses.items():
                raw = self._address_to_raw(address)
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

    def _match_against_licenses(self) -> None:
        bar = progressbar.ProgressBar(initial_value=0, max_value=len(self.raw))
        idx = 0
        bad = {}
        for npi, element in self.raw.items():
            idx += 1
            bar.update(idx)
            if npi in self._npi_map:
                continue
            licenses = element['licenses']
            for license_num, state in licenses.items():
                if state != "NY":
                    continue
                clean, code, is_nysop = LicenseCertMunger.clean_up_nysop_number(
                    license_num)

                if not is_nysop:
                    elts = [x.values() for x in element['names']]
                    bad[license_num] = " ".join([str(x) for x in elts])
                    continue

                if clean in self.nys_license_map:
                    ids = self.nys_license_map[clean]
                    if len(ids) != 1:
                        # Ambiguous
                        continue
                    last_names = self._get_last_names(element)
                    for last_name in last_names:
                        if last_name in ids:
                            self._npi_map[npi] = ids[last_name]
                            break

        print()

    @staticmethod
    def _filter_name(x: str) -> bool:
        if not x:
            return False
        if x.find("(") > -1:
            return False
        if x.find(")") > -1:
            return False
        if x.find("&") > -1:
            return False
        return True

    def _match_against_name(self) -> Set[int]:
        already: int = len(self._npi_map)
        total: int = len(self.raw)

        bar = progressbar.ProgressBar(initial_value=0,
                                      max_value=total - already)
        idx = 0

        query = text("""
        SELECT id
        FROM monday.provider
        WHERE name_tsv @@ :tsq :: TSQUERY
        """)

        ambiguous: Set[int] = set()

        for npi, element in self.raw.items():
            if npi in self._npi_map:
                continue
            idx += 1
            bar.update(idx)
            found: Set[int] = set()
            for name in element['names']:
                tokens = name['first_name'].split(" ")
                tokens += name['last_name'].split(" ")
                raw = list(filter(self._filter_name, tokens))
                ts_query = " & ".join(raw).lower()
                ts_query = ts_query.replace(":", "")

                result: ResultProxy = self._session.execute(query,
                                                            {'tsq': ts_query})
                for record in result.fetchall():
                    found.add(record.id)

            count = len(found)
            if count > 1:
                ambiguous.add(npi)
            elif count == 1:
                self._npi_map[npi] = list(found)[0]
        print()
        return ambiguous

    def _match_multiple_criteria(self) -> Set[int]:

        cred_query = text("""
        SELECT
          pc.provider_id
        FROM monday.providers_credentials AS pc
        WHERE exists(SELECT 1
                     FROM monday.providers_addresses AS pa
                       JOIN monday.address AS addy ON pa.address_id = addy.id 
                       AND addy.zip_code = :zip_code
                     WHERE pa.provider_id = pc.provider_id)
          AND exists(SELECT 1 FROM monday.provider AS provider WHERE 
          provider.id = pc.provider_id AND name_tsv @@ :last_name :: TSQUERY)
              AND pc.credential_id = :credential_id 
        """)

        degree_query = text("""
        SELECT
          pd.provider_id
        FROM monday.providers_degrees AS pd
        WHERE exists(SELECT 1
                     FROM monday.providers_addresses AS pa
                       JOIN monday.address AS addy ON pa.address_id = addy.id 
                       AND addy.zip_code = :zip_code
                     WHERE pa.provider_id = pd.provider_id)
          AND exists(SELECT 1 FROM monday.provider AS provider WHERE 
          provider.id = pd.provider_id AND name_tsv @@ :last_name :: TSQUERY)
              AND pd.degree_id = :degree_id
        """)

        address_query = text("""
        SELECT zip_code
        FROM monday.address
        WHERE raw = :raw_addy
        """)

        ambiguous: Set[int] = set()

        already: int = len(self._npi_map)
        total: int = len(self.raw)

        bar = progressbar.ProgressBar(initial_value=0,
                                      max_value=total - already)
        idx = 0

        for npi, element in self.raw.items():
            if npi in self._npi_map:
                continue

            idx += 1
            bar.update(idx)

            # We need at least one cred
            if len(element['credentials']) < 1:
                continue

            last_names: Set[str] = set()
            for name in element['names']:
                raw_last = name.get("last_name").split(" ")
                raw_last = " & ".join(list(filter(self._filter_name, raw_last)))
                if raw_last:
                    last_names.add(raw_last.lower())

            if not last_names:
                continue

            raw_creds = ";".join(element['credentials'])
            creds = CredentialParser(raw_creds, str(npi))

            if not creds.valid_credentials and not creds.valid_degrees:
                continue

            zips: Set[int] = set()
            for address_time, address in element['addresses'].items():
                args = {"raw_addy": self._address_to_raw(address)}
                result: ResultProxy = self._session.execute(address_query, args)
                records: List[dict] = result.fetchall()
                count = len(records)
                assert count < 2, "Index violation: " + str(args)
                if count:
                    zips.add(records[0].zip_code)

            if not zips:
                continue

            found: Set[int] = set()
            for last_name in last_names:
                args = {"last_name": last_name}
                for zip_code in zips:
                    args['zip_code'] = zip_code
                    for credential in creds.valid_credentials:
                        if credential == "csw":
                            credential = "lcsw"
                        assert credential in self._credential_map, credential
                        # noinspection PyUnresolvedReferences
                        args['credential_id'] = self._credential_map[
                            credential].id
                        result: ResultProxy = self._session.execute(cred_query,
                                                                    args)
                        for record in result.fetchall():
                            found.add(record.provider_id)

                    for degree in creds.valid_degrees:
                        assert degree in self._degree_map, degree
                        # noinspection PyUnresolvedReferences
                        args['degree_id'] = self._degree_map[degree].id
                        r: ResultProxy = self._session.execute(degree_query,
                                                               args)
                        for record in r.fetchall():
                            found.add(record.provider_id)

            if len(found) > 1:
                ambiguous.add(npi)
            elif len(found) == 1:
                self._npi_map[npi] = list(found)[0]

        print()

        return ambiguous

    @staticmethod
    def _get_last_names(raw: dict) -> Set[str]:
        last_names: Set[str] = set()
        for name in raw['names']:
            raw_last = name.get("last_name").strip()
            if raw_last:
                last_names.add(raw_last.lower())
        return last_names

    def enrich(self) -> None:
        phone_munger = PhoneAddyMunger(self._session, False)
        phone_munger.pre_process()

        already: int = len(self._npi_map)
        print("Enriching", already, "providers")
        bar = progressbar.ProgressBar(initial_value=0, max_value=already)
        idx = 0
        for npi, row_id in self._npi_map.items():
            provider = self._session.query(Provider).filter_by(
                id=row_id).one_or_none()
            assert provider, "No record with id " + str(row_id)

            provider.directories.append(self._directory)

            element = self.raw[npi]

            last_names = self._get_last_names(element)

            if provider.last_name.lower() not in last_names:
                print(last_names, provider.name_tsv)
                continue

            creds = CredentialParser(";".join(element['credentials']), str(npi))

            provider.gender = element['gender']

            for degree in creds.valid_degrees:
                assert degree in self._degree_map
                provider.degrees.append(self._degree_map[degree])

            for cred in creds.valid_credentials:
                assert cred in self._credential_map
                provider.credentials.append(self._credential_map[cred])

            for address_time, raw_address in element['addresses'].items():
                raw: str = self._address_to_raw(raw_address)
                address: Address = self._session.query(Address).filter_by(
                    raw=raw).one_or_none()

                assert address
                provider.addresses.append(address)

            number_records: Set[Phone] = set()
            for number in element['phones'].values():
                number_records.update(
                    phone_munger.cleanup_phone_numbers(number))

            for phone_record in number_records:
                phone_record.directory = self._directory.id

            if idx % 1000:
                self._session.commit()

            idx += 1
            bar.update(idx)

        self._session.commit()
        phone_munger.post_process()

    def dedupe(self) -> None:
        self._match_against_licenses()
        ambiguous = self._match_against_name()
        ambiguous_complex = self._match_multiple_criteria()
        print(len(ambiguous), "ambiguous name queries")
        print(len(ambiguous_complex), "ambiguous complex queries")
        print("resolved", len(self._npi_map), "NPI ids")


def _run_from_cli():
    n = NPIImporter()
    n.load()
    n.dedupe()
    # n.add_practice_locations()
    n.enrich()


if __name__ == "__main__":
    _run_from_cli()
