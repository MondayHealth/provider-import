from collections import OrderedDict
from typing import MutableMapping, Mapping

from importer.munger_plugin_base import MungerPlugin
from importer.util import m
from provider.models.payment_methods import PaymentMethod
from provider.models.providers import Provider


class PaymentMunger(MungerPlugin):
    MAPPING: Mapping[str, str] = {
        'ach': 'ach bank transfer',
        'amex': 'american express',
        'hsa': 'health savings account'
    }

    def __init__(self, *args):
        super().__init__(*args)
        self._id_map: MutableMapping[str, PaymentMethod] = {}

    def pre_process(self) -> None:
        for elt in self._session.query(PaymentMethod).all():
            n: str = str(elt.payment_type).split('.')[1].lower()
            self._id_map[n] = elt

            if n in self.MAPPING:
                self._id_map[self.MAPPING[n]] = elt

    def process_row(self, row: OrderedDict, provider: Provider) -> None:
        apm = m(row, 'accepted_payment_methods', str)

        if not apm:
            return

        for methods in apm.split(';'):
            method = methods.strip().lower()
            if not methods:
                print(method, row)
                continue
            provider.payment_methods.append(self._id_map[method])
