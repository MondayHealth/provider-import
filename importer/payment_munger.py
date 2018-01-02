import pprint

from sqlalchemy.orm import Session

from importer.loader import RawTable


class PaymentMunger:
    def __init__(self, session: Session):
        self._session: Session = session

    def process(self, table: RawTable) -> None:
        columns, rows = table.get_table_components()

        methods = set()

        for row in rows:
            tokens = row['accepted_payment_methods'].split(';')
            methods.update([x.strip() for x in tokens])

        pprint.pprint(methods)
