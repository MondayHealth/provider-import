import pprint
from collections import OrderedDict
from typing import Set

from sqlalchemy.orm import Session

from importer.munger_plugin_base import MungerPlugin
from importer.util import m
from provider.models.providers import Provider


class SpecialtyMunger(MungerPlugin):

    def __init__(self, session: Session, debug: bool):
        super().__init__(session, debug)

        if self._debug:
            self._specialties: Set[str] = set()

    def process_row(self, row: OrderedDict, provider: Provider) -> None:
        spec = m(row, 'specialties', str)
        if not spec:
            return

        spec = spec.replace("--", " ")
        spec = spec.replace("-", "")
        spec = spec.replace("(", "")
        spec = spec.replace(")", "")
        spec = spec.replace("&", "and")
        # spec = spec.replace("/", ";")
        spec = spec.replace(",", ";")
        spec = spec.replace("'", "").replace('"', '')

        tokens = spec.split(';')
        dedupe = set()
        for token in tokens:
            dedupe.add(token.strip())

        if self._debug:
            self._specialties.update(dedupe)

    def post_process(self):
        super().pre_process()
        if self._debug:
            pprint.pprint(self._specialties)
