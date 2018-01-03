from collections import OrderedDict
from typing import MutableMapping

from importer.munger_plugin_base import MungerPlugin
from importer.util import m
from provider.models.plans import Plan
from provider.models.providers import Provider


class AcceptedPlanMunger(MungerPlugin):
    def __init__(self, *args):
        super().__init__(*args)
        self._id_map: MutableMapping[int, Plan] = {}

    def pre_process(self) -> None:
        for elt in self._session.query(Plan).all():
            self._id_map[elt.id] = elt

    def process_row(self, row: OrderedDict, provider: Provider) -> None:
        apm = m(row, 'accepted_plan_ids', str)

        if not apm:
            return

        for plan_id in apm.split(';'):
            provider.plans_accepted.append(self._id_map[int(plan_id)])
