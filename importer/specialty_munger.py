import pprint
from collections import OrderedDict
from typing import MutableMapping, Set

from sqlalchemy.orm import Session

from fixtures.specialties import COMPILED_REGEXPS
from importer.munger_plugin_base import MungerPlugin
from importer.util import m
from provider.models.providers import Provider
from provider.models.specialties import Specialty


class SpecialtyMunger(MungerPlugin):

    def __init__(self, session: Session, debug: bool):
        super().__init__(session, debug)

        self._cache: MutableMapping[str, Set[Specialty]] = {}
        self._cache_hits: int = 0

        self._records: MutableMapping[str, Specialty] = {}

        self._unknown_keys: Set[str] = set()

    def pre_process(self) -> None:
        for record in self._session.query(Specialty).all():
            self._records[record.name] = record

    def process_row(self, row: OrderedDict, provider: Provider) -> None:
        raw = m(row, 'specialties', str)

        if not raw:
            return

        # clean it up
        processed = raw.lower().replace("--", " ") \
            .replace("(", "") \
            .replace(")", "") \
            .replace("'", "") \
            .replace('"', '') \
            .replace('.', '') \
            .replace(",", ";")

        found = set()

        for token in processed.split(';'):
            token = token.strip()

            # Edge case, no token
            if not token:
                continue

            if len(token) < 3:
                continue

            # Edge case, we already know there are no specialties for this str
            if token in self._unknown_keys:
                continue

            # Have we never encountered this string before?
            if token not in self._cache:
                detected_specialties = set()
                # If not, test it against all regexes
                for pattern, specialty in COMPILED_REGEXPS:
                    s_record = self._records[specialty]
                    # If we've already added this specialty dont bother matching
                    if s_record in detected_specialties:
                        continue
                    if pattern.search(token):
                        # If it matches record that fact in the cache
                        detected_specialties.add(s_record)
                # Save to the cache to avoid doing this again
                self._cache[token] = detected_specialties
                # If we detected nothing, continue on
                if len(detected_specialties) == 0:
                    self._unknown_keys.add(token)
                    continue
            else:
                self._cache_hits += 1
                detected_specialties = self._cache[token]

            # Save these as having been detected for this provider
            found.update(detected_specialties)

        # Edge case: nothing found
        if len(found) == 0:
            return

        already = {x for x in provider.specialties}

        # Reconcile by doing set disjunction
        for record in found:
            if record not in already:
                provider.specialties.append(record)

    def post_process(self):
        super().post_process()
        if self._debug:
            print()
            print("Specialties cache hits", self._cache_hits)

            print()
            pprint.pprint(self._cache)

            print()
            pprint.pprint(self._unknown_keys)
