from collections import OrderedDict
from typing import Set, MutableMapping

from psycopg2._range import NumericRange
from sqlalchemy.orm import Session

from importer.munger_plugin_base import MungerPlugin
from importer.util import m
from provider.models.providers import Provider, AGE_RANGE_NAMES


class AgeRangeMunger(MungerPlugin):
    AGE_NAMES = frozenset(AGE_RANGE_NAMES)

    # It seems like when people say 6-10 they mean INCLUSIVE of both
    RANGE_BOUNDS = "[]"

    def __init__(self, session: Session, debug: bool):
        super().__init__(session, debug)
        self._range_cache: MutableMapping[str, NumericRange] = {}
        self._missed: Set[str] = set()

    def process_row(self, row: OrderedDict, provider: Provider) -> None:
        raw: str = m(row, 'works_with_ages', str)

        if not raw:
            return

        found_age_groups = set()
        ranges: Set[NumericRange] = set()

        for token in raw.lower().split(';'):
            token = token.strip()
            if not token:
                continue

            if token in self.AGE_NAMES:
                found_age_groups.add(token)
                if token.find("(") > -1:
                    continue

            if token.find("(") < 0:
                continue

            inside = token[token.find("(") + 1:token.find(")")]

            # range cache hit
            if inside in self._range_cache:
                ranges.add(self._range_cache[inside])
                continue

            sub_tokens = inside.split("to")

            # range cache miss
            if len(sub_tokens) > 1:
                val = NumericRange(int(sub_tokens[0]), int(sub_tokens[1]),
                                   bounds=self.RANGE_BOUNDS)
                self._range_cache[inside] = val
                ranges.add(val)
                continue

            sub_token = sub_tokens[0]

            if sub_token[-1:] == "+":
                val = NumericRange(int(sub_token[:-1]), 999,
                                   bounds=self.RANGE_BOUNDS)
                self._range_cache[inside] = val
                ranges.add(val)
                continue

            # Missed!
            self._missed.add(token)

        provider.age_groups = list(found_age_groups)
        provider.age_ranges = list(ranges)

    def post_process(self):
        super().post_process()
        print("Missed:", self._missed)
