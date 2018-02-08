from collections import OrderedDict
from typing import Tuple

from sqlalchemy.orm import load_only, Session

from importer.munger_plugin_base import MungerPlugin
from importer.util import m
from provider.models.license import License
from provider.models.licensor import Licensor
from provider.models.providers import Provider


class LicenseCertMunger(MungerPlugin):
    NYSOP_NAME = "New York State Office of the Professions"

    ABPN_NAME = "American Board of Psychiatry and Neurology"

    def __init__(self, *args):
        super().__init__(*args)
        self._nysop: Licensor = None
        self._abpn: Licensor = None

    @staticmethod
    def get_or_create_nysop(session: Session) -> Licensor:
        # Construct the NYS OP licensor
        nysop: Licensor = session.query(Licensor).filter_by(
            name=LicenseCertMunger.NYSOP_NAME).one_or_none()

        if not nysop:
            print("Constructing", LicenseCertMunger.NYSOP_NAME)
            nysop = Licensor(name=LicenseCertMunger.NYSOP_NAME, state="NY")
            session.add(nysop)
            session.commit()

        return nysop

    def pre_process(self):
        super().pre_process()

        self._nysop: Licensor = self.get_or_create_nysop(self._session)

        abpn = self._session.query(Licensor).filter_by(
            name=self.ABPN_NAME).one_or_none()

        if not abpn:
            print("Constructing", self.ABPN_NAME)
            abpn = Licensor(name=self.ABPN_NAME)
            self._session.add(abpn)
            self._session.commit()

        self._abpn = abpn

    @staticmethod
    def clean_up_nysop_number(raw: str) -> Tuple[str, str, bool]:
        """ Take a random string and see if you can coerce it into a NYSOP
        license. Return a cleaned up version and true if successful, otherwise
        just the input + false. """

        """
        LCSW-R 019020-1
        LMFT000983-1
        PR024933-1
        R-054812-1
        R-017051
        R022822
        NYS Licensed Psychoanalyst # 000789
        68 021594
        R 024794
        002797 & 000259
        """

        cleaned = raw.strip().upper().replace(" ", "").replace("O", "0")
        count = len(cleaned)

        # It might be valid
        test = None
        try:
            test: int = int(cleaned)
        except ValueError:
            pass

        if test is not None:
            # This is ambiguous because it could be a code
            if count > 8 or count < 3:
                return cleaned, "", False
            if count == 8:
                return cleaned[2:], cleaned[:2], True
            if count == 7 and cleaned[-1:] == "1":
                # Probably meant -1, like 0393581
                return cleaned[:-1], "", True
            if count < 7:
                return cleaned.zfill(6), "", True

        # Thanks TERESA >:(
        if cleaned.find("&") > -1:
            cleaned = cleaned.split("&")[0].strip()

        tokens: str = cleaned.replace("#", "-") \
            .replace("NYS", "").replace("NY", "")\
            .replace("LMFT", "").replace("LCSW", "")

        found = None
        code = ""
        for token in tokens.split("-"):
            if not token:
                continue
            if token == "R":
                continue
            if token == "1" or token == "0":
                continue

            if len(token) == 2 and not found:
                try:
                    code = str(int(token)).zfill(2)
                    continue
                except ValueError:
                    pass

            token = token.replace('PR', '')
            token = token.replace('RP', '')
            token = token.replace('R', '')

            try:
                found = int(token)
            except ValueError:
                pass

        if not found:
            return raw, "", False
        if found:
            return str(found).zfill(6), code, True

    def _do_license(self, license_number: str, provider: Provider) -> None:

        cleaned, code, nysop = self.clean_up_nysop_number(license_number)

        if not nysop:
            return

        if not code:
            code = None

        # noinspection PyUnresolvedReferences
        q = self._session.query(License).filter_by(number=cleaned,
                                                   licensor_id=self._nysop.id,
                                                   secondary_number=code)

        lic = q.options(load_only("licensee_id")).one_or_none()

        # Add the nysop license if its not there
        if not lic:
            lic = License(number=cleaned, licensee=provider,
                          licensor=self._nysop, secondary_number=code)

        """
        It's a requirement of association tables in sqlalchemy that the
        "child" in the relationship must be explicitly associated with
        the association record. see:
        docs.sqlalchemy.org/en/latest/orm/basic_relationships.html
        #association-object
        """
        provider.licenses.append(lic)

    def _do_cert(self, cert_number: str, provider: Provider) -> None:
        q = self._session.query(License) \
            .filter_by(number=cert_number, licensor_id=self._abpn.id)
        cert = q.options(load_only("licensee_id")).one_or_none()

        if not cert:
            cert = License(number=cert_number, licensor=self._abpn,
                           licensee=provider)
        provider.licenses.append(cert)

    def process_row(self, row: OrderedDict, provider: Provider) -> None:
        for number in m(row, 'license_number', str, "").split(";"):
            if number:
                self._do_license(number, provider)

        for number in m(row, 'certificate_number', str, "").split(";"):
            if number:
                self._do_cert(number, provider)
