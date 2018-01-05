from collections import OrderedDict

from sqlalchemy.orm import Session, load_only

from importer.munger_plugin_base import MungerPlugin
from importer.orientation_munger import OrientationMunger
from importer.util import m
from provider.models.accepted_payor_comment import AcceptedPayorComment
from provider.models.providers import Provider


class AcceptedPayorsMunger(MungerPlugin):

    def __init__(self, session: Session, debug: bool):
        super().__init__(session, debug)

        self._found = set()

    def process_row(self, row: OrderedDict, provider: Provider) -> None:
        raw: str = m(row, 'accepted_payors', str)

        if not raw:
            return

        replaced_raw = raw.strip().lower() \
            .replace(":", ' ') \
            .replace(")", ' ') \
            .replace("(", ' ') \
            .replace('"', ' ') \
            .replace("/", ';') \
            .replace("out-of-network", 'oon') \
            .replace("out of network", 'oon') \
            .replace("oon -", 'oon ') \
            .replace("oon-", 'oon ') \
            .replace("oon", ";oon;") \
            .replace(".", ';') \
            .replace(",", ';') \
            .replace("=", ' ') \
            .replace("|", ';') \
            .replace("*", ' ') \
            .replace("&", ' and ') \
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

            apc: AcceptedPayorComment = self._session.query(
                AcceptedPayorComment).filter_by(body=token).options(
                load_only('id')).one_or_none()

            if not apc:
                apc = AcceptedPayorComment(body=token)
                self._session.add(apc)

            records.append(apc)
            added.add(token)

        already = {x for x in provider.accepted_payor_comments}

        for record in records:
            if record not in already:
                provider.accepted_payor_comments.append(record)

    def post_process(self):
        super().post_process()
        print("\nUpdating...")
        self._session.execute(
            "UPDATE monday.acceptedpayorcomment SET tsv = to_tsvector("
            "'english', body);")
        print("Done")
