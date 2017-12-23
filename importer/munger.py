import configparser
import re
from collections import OrderedDict
from typing import Mapping, Tuple, List, Union, Iterable

import phonenumbers
import progressbar
from phonenumbers import PhoneNumber, NumberParseException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

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


def _new_phone_from_raw(raw: str) -> Union[Phone, None]:
    try:
        v: PhoneNumber = phonenumbers.parse(raw, "US")
    except NumberParseException:
        return None
    out = str(v.national_number)
    try:
        return Phone(npa=int(out[3:]),
                     nxx=int(out[3:6]),
                     xxxx=int(out[:-4]),
                     extension=v.extension)
    except ValueError:
        return None


def _mux_addy_phone(raw_address: str, raw_phone: str) -> \
        Tuple[List[Address], List[Phone]]:
    a_tokens = raw_address.strip().split("\n")
    addresses = []
    phone_numbers = []
    current = ''
    for token in a_tokens:
        if not token:
            addresses.append(Address(raw=current.strip()))
            current = ''
            continue
        current = current + token.strip() + " "
    addresses.append(Address(raw=current.strip()))

    p_tokens = raw_phone.strip().split("\n")
    for token in p_tokens:
        if not token:
            continue
        phone_numbers.append(_new_phone_from_raw(token.strip()))

    return addresses, phone_numbers


def _provider(table: RawTable, session: Session) -> Iterable[OrderedDict]:
    columns, rows = table.get_table_components()
    i = 0
    failed = []
    bar = progressbar.ProgressBar(max_value=len(rows))
    for row in rows:
        addresses, numbers = _mux_addy_phone(row['address'], row['phone'])
        provider = Provider()
        for address in addresses:
            provider.addresses.append(address)
        for number in numbers:
            if number is None:
                failed.append(row)
                continue
            provider.phone_numbers.append(number)
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
        url = config['alembic']['sqlalchemy.url']
        print("Creating engine at", url)
        self._engine = create_engine(url, echo=ECHO_SQL)
        session_factory = sessionmaker(bind=self._engine)
        self._Session = scoped_session(session_factory)

    def munge(self, tables: Mapping[str, RawTable]) -> None:
        # _locations(tables['locations'])
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
