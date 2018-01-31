from collections import OrderedDict
from typing import Union, List, Set

import phonenumbers
from phonenumbers import PhoneNumber, NumberParseException

from importer.munger_plugin_base import MungerPlugin
from importer.util import m
from provider.models.address import Address
from provider.models.phones import Phone
from provider.models.providers import Provider


class PhoneAddyMunger(MungerPlugin):

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

    def _cleanup_phone_numbers(self, raw_phone: str) -> List[Phone]:
        p = []
        phone_numbers = set()

        for token in raw_phone.split("\n"):
            if token:
                phone_numbers.add(token.strip())
        for pn in phone_numbers:
            nn = self._phone_or_new(pn)
            if nn:
                p.append(nn)

        return p

    @staticmethod
    def parse_raw_address(raw_address: str) -> Set[str]:
        addresses = set()
        current = ''
        for token in raw_address.split("\n"):
            if not token:
                addresses.add(current.strip())
                current = ''
                continue
            current = current + token.strip() + " "
        addresses.add(current.strip())
        return addresses

    def _cleanup_addresses(self, raw_address: str) -> List[Address]:
        ret = []

        for a in self.parse_raw_address(raw_address):
            found = self._session.query(Address).filter_by(raw=a).one_or_none()

            if not found:
                found = Address(raw=a)
                self._session.add(found)

            ret.append(found)

        return ret

    def process_row(self, row: OrderedDict, provider: Provider) -> None:
        raw_address = m(row, 'address', str)
        raw_phone = m(row, 'phone', str)

        # Break up the addy and phones and insert them
        if raw_address:
            for address in self._cleanup_addresses(raw_address):
                provider.addresses.append(address)

        if raw_phone:
            for number in self._cleanup_phone_numbers(raw_phone):
                provider.phone_numbers.append(number)
