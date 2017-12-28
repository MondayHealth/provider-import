import configparser
import datetime
import re
from collections import OrderedDict
from typing import Tuple, List, Union, Iterable, Mapping, TypeVar

import phonenumbers
import progressbar
from phonenumbers import PhoneNumber, NumberParseException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session, load_only

from db_url import get_db_url
from importer.loader import RawTable
from provider.models.address import Address
from provider.models.directories import Directory
from provider.models.license import License
from provider.models.licensor import Licensor
from provider.models.payors import Payor
from provider.models.phones import Phone
from provider.models.plans import Plan
from provider.models.providers import Provider

ECHO_SQL = False

V = TypeVar(str, bool, int)


def int_or_none(row: OrderedDict, name: str) -> None:
    v = row[name]
    if not v:
        row[name] = None
    else:
        row[name] = int(v)


def str_or_none(row: OrderedDict, name: str) -> None:
    v = row[name]
    if not v:
        row[name] = None
    else:
        row[name] = str(v).strip()


def de_camel(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _m(m: Mapping, n: str, t: V, d: Union[None, V] = None) -> Union[None, V]:
    """
    Coerce an element in a mapping by type and key
    :param m: The mapping
    :param n: The name of the key
    :param t: The type expected
    :param d: The default value, should the retrieved value be none
    :return: The value of the type specified in 't' or None
    """
    # Check to see if its present
    if n not in m:
        return d

    # Get the value
    ret = m[n]

    # Try to avoid storing black strings or whitespace at all costs
    if t is str:
        ret = str(ret).strip()
        return ret if ret else d

    # Coerce the final value
    return None if ret is '' else t(ret)


class ProviderMunger:
    NYSOP_NAME = "New York State Office of the Professions"

    def __init__(self, session: Session):
        self._session: Session = session
        self._load_nysop()

    def _load_nysop(self):
        # Construct the NYS OP licensor
        nysop = self._session.query(Licensor).filter_by(
            name=self.NYSOP_NAME).one_or_none()

        if not nysop:
            print("Constructing", self.NYSOP_NAME)
            nysop = Licensor(name=self.NYSOP_NAME, state="NY")
            self._session.add(nysop)

        self._nysop: Licensor = nysop

    def _phone_or_new(self, raw: str) -> Union[Phone, None]:
        if len(raw) < 10:
            print('Too short', raw)
            return None

        try:
            v: PhoneNumber = phonenumbers.parse(raw, "US")
        except NumberParseException:
            print('NPE', raw)
            return None

        if v.national_number > 9999999999:
            print('Skipping bad pn', raw)
            return None

        out = str(v.national_number)
        try:
            inst = Phone(npa=int(out[:3]),
                         nxx=int(out[3:6]),
                         xxxx=int(out[-4:]),
                         extension=v.extension)
        except ValueError:
            print("Value Error", raw)
            return None

        found = self._session.query(Phone).filter_by(npa=inst.npa,
                                                     nxx=inst.nxx,
                                                     xxxx=inst.xxxx,
                                                     extension=inst.extension) \
            .one_or_none()

        if not found:
            self._session.add(inst)
            found = inst

        return found

    def _address_or_new(self, raw: str) -> Address:
        found = self._session.query(Address).filter_by(raw=raw).one_or_none()

        if not found:
            found = Address(raw=raw)
            self._session.add(found)

        return found

    def _mux_addy_phone(self, raw_address: str, raw_phone: str) -> \
            Tuple[List[Address], List[Phone]]:
        a_tokens = raw_address.strip().split("\n")
        addresses = []
        phone_numbers = []
        current = ''
        for token in a_tokens:
            if not token:
                addresses.append(self._address_or_new(current.strip()))
                current = ''
                continue
            current = current + token.strip() + " "
        addresses.append(self._address_or_new(current.strip()))

        p_tokens = raw_phone.strip().split("\n")
        for token in p_tokens:
            if not token:
                continue
            phone_numbers.append(self._phone_or_new(token.strip()))

        return addresses, phone_numbers

    def _find_nysop_license(self, licence_number: str) -> Union[int, None]:
        if not licence_number:
            return None
        q = self._session.query(License).filter_by(number=licence_number,
                                                   licensor_id=self._nysop.id)
        lic = q.options(load_only("licensor_id")).one_or_none()
        return lic.licensor_id if lic else None

    def load_table(self, table: RawTable) -> Iterable[OrderedDict]:
        columns, rows = table.get_table_components()
        now = datetime.datetime.utcnow()
        i = 0
        failed = []
        bar = progressbar.ProgressBar(max_value=len(rows))
        things_to_get = {
            'source_updated_at': str,
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
            'works_with_ages': str
        }

        for row in rows:
            # Determine the user ID via license number for dedup
            license_number = _m(row, 'license_number', str)
            id_via_license = self._find_nysop_license(license_number)
            row_id = id_via_license if id_via_license else row['id']

            # transform the row into args that have been coerced to types
            args = {}
            for k, v in things_to_get.items():
                args[k] = _m(row, k, v)

            updated = self._session.query(Provider).filter_by(id=row_id).update(
                args)

            if updated == 0:
                provider = Provider(id=row_id,
                                    created_at=_m(row, 'created_at', str, now),
                                    updated_at=_m(row, 'updated_at', str, now),
                                    **args)
                self._session.add(provider)
            else:
                provider = self._session.query(Provider).filter_by(
                    id=row_id).options(load_only("id")).one_or_none()

            # Break up the addy and phones
            raw_addy = _m(row, 'address', str)
            raw_phone = _m(row, 'phone', str)
            addresses, numbers = self._mux_addy_phone(raw_addy, raw_phone)

            for address in addresses:
                provider.addresses.append(address)
            for number in numbers:
                if number is None:
                    failed.append(row)
                    continue
                provider.phone_numbers.append(number)

            # Check to see if we need to add a license entry
            if not id_via_license and license_number:
                lic = License(number=license_number, licensee=provider,
                              licensor=self._nysop)
                self._session.add(lic)

            self._session.commit()
            bar.update(i)
            i = i + 1

        return failed


def _directories(table: RawTable, session: Session) -> None:
    columns, rows = table.get_table_components()
    i = 0
    bar = progressbar.ProgressBar(max_value=len(rows))
    for row in rows:
        int_or_none(row, 'record_limit')
        session.merge(Directory(**row))
        bar.update(i)
        i = i + 1


def _payors(table: RawTable, session: Session) -> None:
    columns, rows = table.get_table_components()
    i = 0
    bar = progressbar.ProgressBar(max_value=len(rows))
    for row in rows:
        session.merge(Payor(**row))
        bar.update(i)
        i = i + 1


def _plans(table: RawTable, session: Session) -> None:
    columns, rows = table.get_table_components()
    i = 0
    bar = progressbar.ProgressBar(max_value=len(rows))
    for row in rows:
        int_or_none(row, 'record_limit')
        str_or_none(row, 'original_code')
        session.merge(Plan(**row))
        bar.update(i)
        i = i + 1


class Munger:
    """ Take a bunch of raw tables and create a bulk insertion """

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("alembic.ini")
        url = get_db_url()
        print("Creating engine at", url)
        self._engine = create_engine(url, echo=ECHO_SQL)
        session_factory = sessionmaker(bind=self._engine)
        self._Session = scoped_session(session_factory)
        self._Session.configure()

    def munge(self, tables: Mapping[str, RawTable]) -> None:
        session: Session = self._Session()
        _directories(tables['directories'], session)
        _payors(tables['payors'], session)
        _plans(tables['plans'], session)

        pm = ProviderMunger(session)
        failed = pm.load_table(tables['provider_records'])

        session.commit()
        session.close()

        # Clean up
        print()
        print("Calling ANALYZE...")
        self._engine.execute("ANALYZE;")
        print("Done.")

        print("Failed:")
        for row in failed:
            print(row)
