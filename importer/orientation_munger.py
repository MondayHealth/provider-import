import re
from collections import OrderedDict

from sqlalchemy.orm import load_only

from importer.munger_plugin_base import MungerPlugin
from importer.util import m
from provider.models.orientation import Orientation
from provider.models.providers import Provider


class OrientationMunger(MungerPlugin):
    MULTI_WHITESPACE_STRIP = re.compile(r' +')

    def process_row(self, row: OrderedDict, provider: Provider) -> None:
        raw: str = m(row, 'treatment_orientations', str)

        if not raw:
            return

        replaced_raw = raw.strip().lower() \
            .replace(":", ' ') \
            .replace(")", ' ') \
            .replace("(", ' ') \
            .replace("/", ' ') \
            .replace("&", ' and ') \
            .replace("-", ' ') \
            .replace(".", ' ') \
            .replace(",", ' ') \
            .replace("+", ' ')

        replaced_raw = self.MULTI_WHITESPACE_STRIP.sub(' ', replaced_raw)

        added = set()

        records = []

        for token in replaced_raw.split(';'):
            token = token.strip()

            if not token:
                continue

            if token in added:
                continue

            orientation: Orientation = self._session.query(
                Orientation).filter_by(body=token).options(
                load_only('id')).one_or_none()

            if not orientation:
                orientation = Orientation(body=token)
                self._session.add(orientation)

            records.append(orientation)
            added.add(token)

        already = {x for x in provider.treatment_orientations}

        for record in records:
            if record not in already:
                provider.treatment_orientations.append(record)

    def post_process(self):
        super().post_process()

        print("\nUpdating...")
        result = self._session.execute(
            "UPDATE monday.orientation SET tsv = to_tsvector('english', body);")
        print("Done:", result.fetchone())
