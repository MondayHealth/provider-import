from collections import MutableMapping

import progressbar
from sqlalchemy.orm import Session, load_only, subqueryload

from importer.loader import RawTable
from importer.provider_munger import ProviderMunger
from importer.util import m
from provider.models.licensor import Licensor
from provider.models.plans import Plan
from provider.models.providers import Provider


class AcceptedPlanMunger:

    def __init__(self, session: Session):
        self._session: Session = session
        self._id_map: MutableMapping[int, Plan] = {}
        self._build_id_mapping()

    def _build_id_mapping(self) -> None:
        for elt in self._session.query(Plan).all():
            self._id_map[elt.id] = elt

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
            apm = m(row, 'accepted_plan_ids', str)

            if not apm:
                i = i + 1
                bar.update(i)
                continue

            row_id, lic = ProviderMunger.resolve_provider(row, self._session,
                                                          nysopid)

            p = self._session.query(Provider).filter_by(id=row_id).options(
                load_only("id"),
                subqueryload("plans_accepted")
            ).one_or_none()

            for plan_id in apm.split(';'):
                p.plans_accepted.append(self._id_map[int(plan_id)])

            i = i + 1
            bar.update(i)
