import pprint

import progressbar
from sqlalchemy.orm import Session

from importer.loader import RawTable
from importer.provider_munger import ProviderMunger
from importer.util import m
from provider.models.licensor import Licensor


class SpecialtyMunger:

    def __init__(self, session: Session):
        self._session: Session = session

    def process(self, table: RawTable) -> None:
        # Get the state licensure
        nysop = self._session.query(Licensor).filter_by(
            name=ProviderMunger.NYSOP_NAME).one_or_none()
        nysopid = nysop.id

        # Row by row
        columns, rows = table.get_table_components()

        bar = progressbar.ProgressBar(max_value=len(rows))
        i = 0

        specialties = set()

        for row in rows:
            spec = m(row, 'specialties', str)
            if not spec:
                i += 1
                bar.update(i)
                continue

            spec = spec.replace("--", " ")
            spec = spec.replace("-", "")
            spec = spec.replace("(", "")
            spec = spec.replace(")", "")
            spec = spec.replace("&", "and")
            #spec = spec.replace("/", ";")
            spec = spec.replace(",", ";")
            spec = spec.replace("'", "").replace('"', '')

            tokens = spec.split(';')
            dedupe = set()
            for token in tokens:
                dedupe.add(token.strip())

            specialties.update(dedupe)
            i += 1
            bar.update(i)

        pprint.pprint(specialties)
