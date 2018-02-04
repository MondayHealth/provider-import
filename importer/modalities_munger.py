import re
from collections import OrderedDict

from sqlalchemy.orm import load_only

from importer.munger_plugin_base import MungerPlugin
from importer.orientation_munger import OrientationMunger
from importer.util import m
from provider.models.modalities import Modality
from provider.models.providers import Provider


class ModalityMunger(MungerPlugin):
    PSYCHO_SUFFIX = re.compile(r'psycho$')

    def process_row(self, row: OrderedDict, provider: Provider) -> None:
        raw: str = m(row, 'modalities', str)

        # services from GT should be parsed in the same way as modality
        directory_id: int = m(row, "directory_id", int)
        if directory_id == 3:
            raw += " " + m(row, "services", str, "")

        if not raw:
            return

        replaced_raw = raw.strip().lower() \
            .replace(":", ' ') \
            .replace("&", ' and ') \
            .replace(")", ' ') \
            .replace("(", ' ') \
            .replace('"', ' ') \
            .replace("-", ' ') \
            .replace(".", ' ') \
            .replace(",", ' ') \
            .replace("=", ' ') \
            .replace("|", ' ') \
            .replace("®", '') \
            .replace('©', '') \
            .replace('†', '') \
            .replace("*", ' ') \
            .replace("for ", ' ') \
            .replace("rational emotive behavioral", 'rebt') \
            .replace("rational emotive behavior", 'rebt') \
            .replace("psychotherapies", "psychotherapy") \
            .replace('therapy', ';therapy;') \
            .replace('psychotherapy', ';psychotherapy;') \
            .replace('psychology', ';psychology;') \
            .replace('psychoanalysis', ';psychoanalysis;') \
            .replace('couples', ';couples;') \
            .replace('couple', ';couples;') \
            .replace('/', ';') \
            .replace("+", ' ')

        replaced_raw = OrientationMunger.MULTI_WHITESPACE_STRIP \
            .sub(' ', replaced_raw)

        replaced_raw = self.PSYCHO_SUFFIX.sub(';psychotherapy;', replaced_raw)

        """
        for token in replaced_raw.split(';'):
            token = token.strip()
            self._found.add(token)
        """

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

            modality: Modality = self._session.query(Modality).filter_by(
                name=token).options(load_only('id')).one_or_none()

            if not modality:
                modality = Modality(name=token)
                self._session.add(modality)

            records.append(modality)
            added.add(token)

        already = {x for x in provider.modalities}

        for record in records:
            if record not in already:
                provider.modalities.append(record)
