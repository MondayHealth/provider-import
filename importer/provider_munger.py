from collections import OrderedDict
from typing import Union, Tuple, List, Mapping, Any, Iterable

import phonenumbers
import progressbar
from phonenumbers import PhoneNumber, NumberParseException
from sqlalchemy.orm import Session, load_only

from importer.loader import RawTable
from importer.util import m
from provider.models.address import Address
from provider.models.license import License
from provider.models.licensor import Licensor
from provider.models.phones import Phone
from provider.models.providers import Provider


class ProviderMunger:
    NYSOP_NAME = "New York State Office of the Professions"

    ROW_FIELDS = {
        'source_updated_at': str,
        'created_at': str,
        'updated_at': str,
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

    def __init__(self, session: Session):
        self._session: Session = session
        self._load_nysop()

    @staticmethod
    def _clean_pn(raw: str) -> Union[str, None]:
        """
        Try to recover from

        (212) 947-7111 ext. EXT 528
        (718) 583-0174 ext. X233
        (718) 261-3330 ext. EXT221

        :param raw: the problem pn
        :return: a fixed one or none
        """
        return raw.replace("ext.", "")

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
            cleaned = self._clean_pn(raw)
            if cleaned:
                try:
                    v: PhoneNumber = phonenumbers.parse(cleaned, "US")
                except NumberParseException:
                    print('Skipping bad pn', raw)
                    return None

        out = str(v.national_number)

        args = {
            'npa': int(out[:3]),
            'nxx': int(out[3:6]),
            'xxxx': int(out[-4:]),
            'extension': v.extension
        }

        found = self._session.query(Phone).filter_by(**args).one_or_none()

        if not found:
            inst = Phone(**args)
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

        addresses = []
        phone_numbers = []

        if raw_address:
            current = ''
            for token in raw_address.split("\n"):
                if not token:
                    addresses.append(self._address_or_new(current.strip()))
                    current = ''
                    continue
                current = current + token.strip() + " "
            addresses.append(self._address_or_new(current.strip()))

        if raw_phone:
            for token in raw_phone.split("\n"):
                if not token:
                    continue
                np = self._phone_or_new(token.strip())
                if np:
                    phone_numbers.append(np)

        return addresses, phone_numbers

    def _upsert_row(self, row: Mapping[str, Any]) -> None:
        license_number = m(row, 'license_number', str)
        row_id = m(row, 'id', int)

        # Try to find a license number
        lic: Union[License, None] = None
        if license_number:
            q = self._session.query(License)
            q = q.filter_by(number=license_number, licensor_id=self._nysop.id)
            lic = q.options(load_only("licensee_id")).one_or_none()
            if lic:
                row_id = lic.licensee_id

        # Make the new provider record
        args = {}
        for k, v in self.ROW_FIELDS.items():
            val = m(row, k, v)
            # This check is important because we want fields that are set to
            # null to not overwrite existing fields from other record sources
            if val is not None:
                args[k] = val
        provider = Provider(id=row_id, **args)
        provider = self._session.merge(provider)

        # Break up the addy and phones and insert them
        raw_addy = m(row, 'address', str)
        raw_phone = m(row, 'phone', str)
        addresses, numbers = self._mux_addy_phone(raw_addy, raw_phone)
        provider.addresses = provider.addresses + addresses
        provider.phone_numbers = provider.phone_numbers + numbers

        # If we haven't created this license yet, do it.
        if not lic and license_number:
            lic = License(number=license_number, licensee=provider,
                          licensor=self._nysop)

            # This should be new
            self._session.add(lic)

    def load_table(self, table: RawTable) -> Iterable[OrderedDict]:
        columns, rows = table.get_table_components()
        i = 0
        failed = []
        bar = progressbar.ProgressBar(max_value=len(rows))
        for row in rows:
            self._upsert_row(row)
            self._session.commit()
            bar.update(i)
            i = i + 1

        return failed