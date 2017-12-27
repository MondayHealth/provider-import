import configparser
import datetime
import re
from collections import OrderedDict
from typing import Tuple, List, Union, Iterable, Mapping, TypeVar

import phonenumbers
import progressbar
from phonenumbers import PhoneNumber, NumberParseException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from db_url import get_db_url
from importer.loader import RawTable
from provider.models.address import Address
from provider.models.directories import Directory
from provider.models.payors import Payor
from provider.models.phones import Phone
from provider.models.plans import Plan
from provider.models.providers import Provider

ECHO_SQL = False


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
        row[name] = str(v)


def de_camel(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _phone_or_new(raw: str, session: Session) -> Union[Phone, None]:
    try:
        v: PhoneNumber = phonenumbers.parse(raw, "US")
    except NumberParseException:
        return None
    if v.national_number > 9999999999:
        print('Skipping bad pn: ' + raw)
        return None
    out = str(v.national_number)
    try:
        inst = Phone(npa=int(out[3:]),
                     nxx=int(out[3:6]),
                     xxxx=int(out[:-4]),
                     extension=v.extension)
    except ValueError:
        return None

    found = session.query(Phone).filter_by(npa=inst.npa,
                                           nxx=inst.nxx,
                                           xxxx=inst.xxxx,
                                           extension=inst.extension) \
        .one_or_none()

    if not found:
        session.add(inst)
        found = inst

    return found


def _address_or_new(raw: str, session: Session) -> Address:
    found = session.query(Address).filter_by(raw=raw).one_or_none()
    if not found:
        found = Address(raw=raw)
        session.add(found)
    return found


def _mux_addy_phone(raw_address: str, raw_phone: str, session: Session) -> \
        Tuple[List[Address], List[Phone]]:
    a_tokens = raw_address.strip().split("\n")
    addresses = []
    phone_numbers = []
    current = ''
    for token in a_tokens:
        if not token:
            addresses.append(_address_or_new(current.strip(), session))
            current = ''
            continue
        current = current + token.strip() + " "
    addresses.append(_address_or_new(current.strip(), session))

    p_tokens = raw_phone.strip().split("\n")
    for token in p_tokens:
        if not token:
            continue
        phone_numbers.append(_phone_or_new(token.strip(), session))

    return addresses, phone_numbers


V = TypeVar(str, bool, int)


def _m(m: Mapping, n: str, t: V, d: Union[None, V] = None) -> Union[None, V]:
    if n not in m:
        return d
    ret = m[n]
    if ret == '':
        return d
    return t(ret)


def _provider(table: RawTable, session: Session) -> Iterable[OrderedDict]:
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
        provider = session.query(Provider).filter_by(id=row['id']).one_or_none()
        addresses, numbers = _mux_addy_phone(row['address'],
                                             row['phone'],
                                             session)
        args = {}
        for k, v in things_to_get.items():
            args[k] = _m(row, k, v)
        provider = Provider(id=row['id'],
                            created_at=_m(row, 'created_at', str, now),
                            updated_at=_m(row, 'updated_at', str, now),
                            **args)
        for address in addresses:
            provider.addresses.append(address)
        for number in numbers:
            if number is None:
                failed.append(row)
                continue
            provider.phone_numbers.append(number)
        session.merge(provider)
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

    def munge(self, tables: Mapping[str, RawTable]) -> None:
        session: Session = self._Session()
        _directories(tables['directories'], session)
        _payors(tables['payors'], session)
        _plans(tables['plans'], session)
        failed = _provider(tables['provider_records'], session)
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
