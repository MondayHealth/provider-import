from typing import MutableMapping, Mapping

import progressbar
from sqlalchemy.orm import Session, load_only, subqueryload

from importer.loader import RawTable
from importer.provider_munger import ProviderMunger
from importer.util import m
from provider.models.licensor import Licensor
from provider.models.payment_methods import PaymentMethod
from provider.models.providers import Provider


class PaymentMunger:
    MAPPING: Mapping[str, str] = {
        'ach': 'ach bank transfer',
        'amex': 'american express',
        'hsa': 'health savings account'
    }

    def __init__(self, session: Session):
        self._session: Session = session
        self._id_map: MutableMapping[str, PaymentMethod] = {}
        self._build_id_mapping()

    def _build_id_mapping(self) -> None:
        for elt in self._session.query(PaymentMethod).all():
            n: str = str(elt.payment_type).split('.')[1].lower()
            self._id_map[n] = elt

            if n in self.MAPPING:
                self._id_map[self.MAPPING[n]] = elt

    def process(self, table: RawTable) -> None:
        # Get the state licensure
        nysop = self._session.query(Licensor).filter_by(
            name=ProviderMunger.NYSOP_NAME).one_or_none()
        nysopid = nysop.id

        # Row by row
        columns, rows = table.get_table_components()

        bar = progressbar.ProgressBar(max_value=len(rows))
        i = 0
        for row in rows:
            apm = m(row, 'accepted_payment_methods', str)

            if not apm:
                i = i + 1
                bar.update(i)
                continue

            row_id, lic = ProviderMunger.resolve_provider(row, self._session,
                                                          nysopid)

            p = self._session.query(Provider).filter_by(id=row_id).options(
                load_only("id"),
                subqueryload("payment_methods")
            ).one_or_none()

            for methods in apm.split(';'):
                method = methods.strip().lower()
                if not methods:
                    print(method, row)
                    continue
                p.payment_methods.append(self._id_map[method])
