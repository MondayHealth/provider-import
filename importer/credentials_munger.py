from collections import OrderedDict
from typing import List

import progressbar
from sqlalchemy.orm import Session

from importer.credential_parser import CredentialParser, print_cred_stats
from importer.loader import RawTable


class CredentialsMunger:
    def __init__(self, session: Session):
        self._session: Session = session
        self._credentials: List[CredentialParser, OrderedDict] = []

    def process(self, table: RawTable) -> None:
        columns, rows = table.get_table_components()

        bar = progressbar.ProgressBar(max_value=len(rows))
        i = 0
        for row in rows:
            d = "{:<30} {}".format(row['first_name'] + " " + row['last_name'],
                                   row['license'])
            self._credentials.append(CredentialParser(row['license'], d))
            bar.update(i)
            i = i + 1

    def print_skipped(self):
        print_cred_stats(self._credentials)
