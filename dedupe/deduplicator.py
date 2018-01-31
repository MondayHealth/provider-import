import configparser
from collections import OrderedDict
from typing import Mapping, List, Set, MutableMapping

import progressbar
import xlsxwriter
from redis import StrictRedis
from sqlalchemy import create_engine, func
from sqlalchemy.orm import scoped_session, sessionmaker, Session, load_only

from db_url import get_db_url
from importer.loader import RawTable
from importer.phone_addy_munger import PhoneAddyMunger
from importer.util import m
from provider.models.address import Address
# noinspection PyUnresolvedReferences
from provider.models.providers import Provider

ZIP_HASH = "ZIPS"

REDIS: StrictRedis = StrictRedis()


class Record:

    def __init__(self, row: OrderedDict):
        self.last_name = None
        self.first_name: str = None
        self.ids: Set[str] = set()
        self.rows: List[OrderedDict] = []
        self.directories: Set[str] = set()
        self.zips: Set[str] = set()
        self.licenses: Set[str] = set()
        self.certificates: Set[str] = set()
        self.first_initials: Set[str] = set()

        self.merge(row)

    def merge(self, row: OrderedDict):
        ln: str = m(row, 'last_name', str, "")
        assert ln, "no last name"
        ln = "".join(ln.replace(".", "").split()).lower()
        if self.last_name:
            assert ln == self.last_name, "differing last name merge"
        else:
            self.last_name = ln

        row_id: str = m(row, 'id', str)
        assert row_id, "no row id"
        self.ids.add(row_id)

        raw_addresses: str = m(row, 'address', str)
        if raw_addresses:
            for address in PhoneAddyMunger.parse_raw_address(raw_addresses):
                z = REDIS.hget(ZIP_HASH, address)
                if z:
                    self.zips.add(z.decode())

        cert_number = m(row, 'certificate_number', str)
        if cert_number:
            self.certificates.add(cert_number)

        license_number = m(row, 'license_number', str)
        if license_number:
            try:
                license_number = str(int(license_number))
            except ValueError:
                pass
            self.licenses.add(license_number)

        directory_id: str = m(row, 'directory_id', str, None)
        if not directory_id:
            directory_id = m(row, 'payor_id', str, None)
            if not directory_id:
                raise Exception("XXX", "no directory or payor")
        self.directories.add(directory_id)

        fn: str = m(row, 'first_name', str, "")
        fn = "".join(fn.replace(".", "").split()).lower()
        if fn:
            if not self.first_name:
                self.first_name = fn
            self.first_initials.add(fn[:2])

        self.rows.append(row)

    def is_same_person(self, other: 'Record') -> bool:
        # If the provider IDs are the same, they're the same person
        if self.ids.intersection(other.ids):
            return True

        # If they have different last names they're not the same
        if other.last_name != self.last_name:
            return False

        # If they have the same certificate number, they're the same
        if other.certificates.intersection(self.certificates):
            return True

        # If they have the same license number they're the same
        if other.licenses.intersection(self.licenses):
            return True

        if other.zips.intersection(
                self.zips) and other.first_initials.intersection(
            self.first_initials):
            return True

        return False


class Deduplicator:
    """ Scan a data source (say, provider_records.xls) and generate a record
    map from its IDs to a unique, incrementing id in Redis. """

    def __init__(self):
        self.uniques_by_last_name: MutableMapping[str, List[Record]] = {}

    def build_index(self, tables: Mapping[str, RawTable]) -> None:
        table = tables['provider_records']
        columns, rows = table.get_table_components()

        records_by_last_name: MutableMapping[str, List[Record]] = {}

        i = 0
        bar = progressbar.ProgressBar(max_value=len(rows), initial_value=i)
        for row in rows:
            r = Record(row)
            if r.last_name not in records_by_last_name:
                records_by_last_name[r.last_name] = [r]
            else:
                records_by_last_name[r.last_name].append(r)
            i += 1
            bar.update(i)

        total = 0
        i = 0
        bar = progressbar.ProgressBar(max_value=len(records_by_last_name),
                                      initial_value=i)
        for last_name, records in records_by_last_name.items():
            uniques: List[Record] = []
            while len(records) > 0:
                record: Record = records.pop()
                found: bool = False
                for unique in uniques:
                    if unique.is_same_person(record):
                        for row in record.rows:
                            unique.merge(row)
                        found = True
                if not found:
                    uniques.append(record)
            self.uniques_by_last_name[last_name] = uniques
            total += len(uniques)
            i += 1
            bar.update(i)

    def csv(self):
        # Create an new Excel file and add a worksheet.
        workbook = xlsxwriter.Workbook('out.xlsx')
        worksheet = workbook.add_worksheet()

        # Widen the first column to make the text clearer.
        worksheet.set_column('A:A', 20)

        # Add a bold format to use to highlight cells.
        bold = workbook.add_format({'bold': True})
        worksheet.write_string(0, 0, "first", bold)
        worksheet.write_string(0, 1, "last", bold)
        worksheet.write_string(0, 2, "dir", bold)
        worksheet.write_string(0, 3, "license", bold)
        worksheet.write_string(0, 4, "zip", bold)
        worksheet.write_string(0, 5, "address", bold)

        # Write some simple text.
        row_index = 1
        for last_name, uniques in self.uniques_by_last_name.items():
            if len(uniques) < 2:
                continue
            for unique in uniques:
                addresses = ""
                licenses = ""
                directories = ";".join(unique.directories)
                for row in unique.rows:
                    addresses += row['address'] + " ; "
                    licenses += row['license'] + " ; "
                worksheet.write_string(row_index, 0, unique.first_name)
                worksheet.write_string(row_index, 1, unique.last_name)
                worksheet.write_string(row_index, 2, directories)
                worksheet.write_string(row_index, 3, licenses)
                worksheet.write_string(row_index, 4, ";".join(unique.zips))
                worksheet.write_string(row_index, 5, addresses)
                row_index += 1

        workbook.close()

    def build_zip_map(self):
        config = configparser.ConfigParser()
        config.read("alembic.ini")
        url = get_db_url()
        print("Creating engine at", url)
        engine = create_engine(url, echo=False)
        session_factory = sessionmaker(bind=engine)
        ss = scoped_session(session_factory)
        ss.configure()
        session: Session = ss()

        f = Address.zip_code.isnot(None)
        count = session.query(func.count(Address.id)).filter(f).scalar()
        query = session.query(Address).options(
            load_only('raw', 'zip_code')).filter(f)

        print("Selecting", count, "addresses")
        rows: List[Address] = query.all()
        print("Complete")

        pbar = progressbar.ProgressBar(max_value=count, initial_value=0)
        i = 0
        for row in rows:
            self._r.hset(ZIP_HASH, row.raw, row.zip_code)
            i += 1
            pbar.update(i)
