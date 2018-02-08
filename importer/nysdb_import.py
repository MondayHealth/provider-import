from datetime import datetime
from typing import List, Union, MutableMapping, Set

import progressbar
from sqlalchemy import text
from sqlalchemy.engine import ResultProxy
from sqlalchemy.orm import Session

from importer.license_cert_munger import LicenseCertMunger
from importer.npi_import import NPIImporter
from importer.phone_addy_munger import PhoneAddyMunger
from provider.models.address import Address
from provider.models.degree import Degree
from provider.models.directories import Directory
from provider.models.license import License
from provider.models.licensor import Licensor
from provider.models.providers import Provider


class RawLine:
    DATE_FMT: str = '%m/%d/%y'

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
        self.regents_action: bool = raw[156] == "*"

        # @TODO: This is not properly documented
        self._priviledge_codes = raw[157:159]

        self.license_date: datetime = datetime.strptime(raw[160:168].strip(),
                                                        self.DATE_FMT)
        self.registration_ending_date: str = raw[168:172]
        self.child_abuse_code: str = raw[172]
        self.infectious_disease_code: str = raw[173]

        self.degree_date: Union[None, datetime] = None
        raw_degree_date: str = raw[174:182].strip()
        if raw_degree_date:
            self.degree_date = datetime.strptime(raw_degree_date, self.DATE_FMT)

        self.school: str = raw[182:207].strip()
        self.email: str = raw[207:247].strip()
        self.phone: str = raw[247:].strip()

        self.full_license_match: Set[int] = set()
        self.license_number_match: Set[int] = set()
        self.name_zip_match: Set[int] = set()
        self.degree_name_match: Set[int] = set()

    def hash(self) -> str:
        return "{}{}:{}".format(self.profession_code,
                                self.license_number,
                                "".join(self.names))

    def get_address(self) -> str:
        components = self.address + [self.city, self.state]
        if self.zip:
            components.append(str(self.zip))
        return " ".join(components)

    def matched(self) -> bool:
        if self.full_license_match or self.license_number_match \
                or self.degree_name_match or self.name_zip_match:
            return True
        return False


class NYSDBImporter:
    PATH: str = "/Users/ixtli/Downloads/monday/nysdb.txt"

    FULL_NAME: str = "New York Office of Professions"

    def __init__(self) -> None:
        self._session: Session = NPIImporter.get_session()

        self._enriched: MutableMapping[int, RawLine] = {}

        self._rows: List[RawLine] = []
        self._row_by_number: MutableMapping[int, List[RawLine]] = {}
        self._relevant_degrees: Set[int] = self._get_relevant_degrees()
        self._directory: Directory = self._get_directory()
        self._licensor: Licensor = LicenseCertMunger.get_or_create_nysop(
            self._session)

        self._phone_munger: PhoneAddyMunger = None

        self._ambiguous: MutableMapping[int, List[RawLine]] = {}
        self._matches: MutableMapping[int, RawLine] = {}

    def _get_relevant_degrees(self) -> Set[int]:
        ret: Set[int] = set()
        things_im_interested_in = {"phd", "psyd", "dph"}
        degrees: List[Degree] = self._session.query(Degree).all()
        for degree in degrees:
            if degree.acronym.lower() in things_im_interested_in:
                # noinspection PyUnresolvedReferences
                ret.add(degree.id)
        return ret

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
            raw = RawLine(line)
            self._rows.append(raw)

            if raw.license_number in self._row_by_number:
                self._row_by_number[raw.license_number].append(raw)
            else:
                self._row_by_number[raw.license_number] = [raw]

            idx += 1
            bar.update(idx)

    def match_rows_to_license_records(self) -> None:
        license_q = text("""
        SELECT licensee_id, number, secondary_number
        FROM monday.license
        WHERE licensor_id = 1
        """)

        print("Getting licenses...")
        result: ResultProxy = self._session.execute(license_q)
        licenses: MutableMapping[int, MutableMapping[int, Set[int]]] = {}
        total_licenses = 0
        for record in result.fetchall():
            total_licenses += 1
            lid = int(record.licensee_id)
            number = int(record.number)
            secondary = None

            if record.secondary_number:
                secondary = int(record.secondary_number)

            lic_num = licenses.get(number, None)
            if lic_num is None:
                licenses[number] = {secondary: {lid}}
            else:
                if secondary in lic_num:
                    licenses[number][secondary].add(lid)
                else:
                    licenses[number][secondary] = {lid}

            if number in self._row_by_number:
                rows = self._row_by_number[number]
                for row in rows:
                    if secondary:
                        if row.profession_code == secondary:
                            row.full_license_match.add(lid)
                    else:
                        row.license_number_match.add(lid)
        print("Done.")

    def complex_match_rows(self) -> None:
        count = len(self._rows)
        bar = progressbar.ProgressBar(initial_value=0, max_value=count)
        idx = 0

        provider_x_name = text("""
        SELECT DISTINCT
          id,
          first_name,
          last_name
        FROM monday.provider AS p
          JOIN monday.providers_addresses AS pa ON p.id = pa.provider_id
        WHERE name_tsv @@ :tsq :: TSQUERY
              AND address_id IN (SELECT id
                                 FROM monday.address
                                 WHERE zip_code = :zip );
        """)

        degree_query_text = text("""
        SELECT DISTINCT
          p.id,
          p.first_name,
          p.last_name
         FROM monday.provider AS p
          JOIN monday.providers_degrees ON p.id = providers_degrees.provider_id
                                           AND providers_degrees.degree_id IN 
                                           ({})
        WHERE name_tsv @@ :tsq :: TSQUERY;
        """.format(",".join([str(x) for x in self._relevant_degrees])))

        for row in self._rows:
            idx += 1
            bar.update(idx)

            # Special case, there's no reason to recheck
            if len(row.full_license_match):
                continue

            last_name = list(filter(None, row.names))[0].lower()

            result: ResultProxy = self._session.execute(provider_x_name, {
                "tsq": last_name,
                "zip": row.zip
            })

            for record in result.fetchall():
                row.name_zip_match.add(record.id)

            if row.profession_code == 68:
                result = self._session.execute(degree_query_text,
                                               {'tsq': last_name})
                for record in result.fetchall():
                    row.degree_name_match.add(record.id)

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

    def _update_provider_using_row(self, pid: int, row: RawLine) -> None:

        provider: Provider = self._session.query(Provider).filter_by(
            id=pid).one_or_none()

        if pid in self._enriched:
            print("!! Double:", pid, self._enriched[pid].hash(), "(",
                  row.hash(),
                  provider.first_name,
                  provider.last_name, ")")
            return

        provider.directories.append(self._directory)

        if row.email:
            provider.email = row.email

        if row.school:
            provider.school = row.school

        if row.degree_date:
            provider.year_graduated = row.degree_date.year

        if row.phone:
            for phone in self._phone_munger.cleanup_phone_numbers(row.phone):
                if not phone.directory:
                    # noinspection PyUnresolvedReferences
                    phone.directory = self._directory.id
                provider.phone_numbers.append(phone)

        if "".join(row.address).strip():
            q = self._session.query(Address).filter_by(raw=row.get_address())
            address: Address = q.one_or_none()
            assert address
            provider.addresses.append(address)

        code = str(row.profession_code)
        num = str(row.license_number).zfill(6)
        most_accurate: Union[bool, License] = False
        for lic in provider.licenses:
            # noinspection PyUnresolvedReferences
            if lic.licensor_id != self._licensor.id:
                continue
            if lic.secondary_number == code and lic.number == num:
                if not lic.granted:
                    lic.granted = row.license_date
                most_accurate = True
                break
            if lic.number == num and not lic.secondary_number:
                most_accurate = lic
                continue

        if most_accurate is False:
            lic = License(licensee=provider, licensor=self._licensor,
                          number=num, secondary_number=code,
                          granted=row.license_date)
            provider.licenses.append(lic)
        elif most_accurate is not True:
            assert not most_accurate.secondary_number
            most_accurate.secondary_number = code
            most_accurate.granted = row.license_date

        self._enriched[pid] = row

    def _mark_ambiguous(self, pid: int, row: RawLine):
        if pid not in self._ambiguous:
            self._ambiguous[pid] = []
        self._ambiguous[pid].append(row)

    def _match(self, pid: int, row: RawLine) -> None:
        if pid in self._ambiguous:
            self._mark_ambiguous(pid, row)
        elif pid in self._matches and self._matches[pid] != row:
            self._mark_ambiguous(pid, self._matches[pid])
            self._mark_ambiguous(pid, row)
            del self._matches[pid]
        else:
            self._matches[pid] = row

    def _do_matches(self) -> None:
        self._phone_munger: PhoneAddyMunger = PhoneAddyMunger(self._session,
                                                              False)
        self._phone_munger.pre_process()

        print("\nEnriching matches...")
        count = len(self._matches)
        idx = 0
        bar = progressbar.ProgressBar(initial_value=idx, max_value=count)
        for pid, row in self._matches.items():
            self._update_provider_using_row(pid, row)

            if idx % 250:
                self._session.commit()
            idx += 1
            bar.update(idx)

        self._session.commit()
        self._phone_munger.post_process()
        print("\nDone.")

    def _print_ambiguous(self) -> None:
        print("Printing", len(self._ambiguous), "ambiguous matches.")
        for pid, rows in self._ambiguous.items():
            provider: Provider = self._session.query(Provider).filter_by(
                id=pid).one_or_none()
            print(pid, provider.first_name, provider.last_name)
            for row in rows:
                print("\t-", row.hash())

    def enrich(self) -> None:

        print("Gathering matched rows...")
        gathered: List[RawLine] = [r for r in self._rows if r.matched()]
        print("Done")

        weak_matches: MutableMapping[int, List[RawLine]] = {}

        total_rows = len(self._rows)
        idx = 0
        bar = progressbar.ProgressBar(initial_value=idx, max_value=total_rows)
        for row in gathered:
            # Do exact matches first
            found_count: int = len(row.full_license_match)
            assert found_count < 2

            if found_count == 1:
                for pid in row.full_license_match:
                    self._match(pid, row)
                continue

            # Now do really high correlation ones
            found: Set[int] = set()
            for pid in row.license_number_match:
                name_zip = pid in row.name_zip_match
                name_degree = pid in row.degree_name_match
                if name_zip or name_degree:
                    found.add(pid)

            found_count = len(found)
            assert found_count < 2

            if found_count == 1:
                self._match(list(found)[0], row)
                continue

            # Now relate two things which might be tough
            found = row.name_zip_match.intersection(row.degree_name_match)
            found_count = len(found)

            if found_count == 1:
                self._match(list(found)[0], row)
            if found_count > 1:
                for pid in found:
                    if pid not in weak_matches:
                        weak_matches[pid] = [row]
                    else:
                        weak_matches[pid].append(row)

            idx += 1
            bar.update(idx)

        self._do_matches()

        self._print_ambiguous()

        print("Weak matches:", len(weak_matches))
        print("Enriched", len(self._enriched), "records")


def _run_from_cli():
    n = NYSDBImporter()
    n.load()
    # n.add_new_addresses()
    # n.test_munger()
    n.match_rows_to_license_records()
    n.complex_match_rows()

    n.enrich()


if __name__ == "__main__":
    _run_from_cli()
