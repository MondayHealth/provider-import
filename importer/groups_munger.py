from collections import OrderedDict

from sqlalchemy.orm import load_only

from importer.munger_plugin_base import MungerPlugin
from importer.orientation_munger import OrientationMunger
from importer.util import m
from provider.models.groups import Group
from provider.models.providers import Provider


class GroupsMunger(MungerPlugin):
    def process_row(self, row: OrderedDict, provider: Provider) -> None:
        raw: str = m(row, 'works_with_groups', str)

        if not raw:
            return

        replaced_raw = raw.strip().lower() \
            .replace(":", ' ') \
            .replace(")", ' ') \
            .replace("(", ' ') \
            .replace('"', ' ') \
            .replace("'", ' ') \
            .replace("/", ';') \
            .replace("&", ' and ') \
            .replace("-", ' ') \
            .replace(".", ' ') \
            .replace(",", ' ') \
            .replace("+", ' ')

        replaced_raw = OrientationMunger.MULTI_WHITESPACE_STRIP \
            .sub(' ', replaced_raw)

        if not replaced_raw:
            return

        added = set()

        records = []

        for token in replaced_raw.split(';'):
            token = token.strip()

            if not token:
                continue

            if token in added:
                continue

            group: Group = self._session.query(Group).filter_by(
                body=token).options(load_only('id')).one_or_none()

            if not group:
                group = Group(body=token)
                self._session.add(group)

            records.append(group)
            added.add(token)

        already = {x for x in provider.groups}

        for record in records:
            if record not in already:
                provider.groups.append(record)

    def post_process(self):
        super().post_process()

        print("\nUpdating...")
        self._session.execute(
            "UPDATE monday.group SET tsv = to_tsvector('english', body);")
        print("Done")
