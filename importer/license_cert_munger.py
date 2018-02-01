from collections import OrderedDict

from sqlalchemy.orm import load_only

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

    def pre_process(self):
        super().pre_process()

        # Construct the NYS OP licensor
        nysop = self._session.query(Licensor).filter_by(
            name=self.NYSOP_NAME).one_or_none()

        if not nysop:
            print("Constructing", self.NYSOP_NAME)
            nysop = Licensor(name=self.NYSOP_NAME, state="NY")
            self._session.add(nysop)

        self._nysop: Licensor = nysop

        abpn = self._session.query(Licensor).filter_by(
            name=self.ABPN_NAME).one_or_none()

        if not abpn:
            print("Constructing", self.ABPN_NAME)
            abpn = Licensor(name=self.ABPN_NAME)
            self._session.add(abpn)

        self._abpn = abpn

    def process_row(self, row: OrderedDict, provider: Provider) -> None:
        license_number: str = m(row, 'license_number', str)

        if license_number:
            q = self._session.query(License).filter_by(
                number=license_number, licensor_id=self._nysop.id)
            lic = q.options(load_only("licensee_id")).one_or_none()

            # Add the nysop license if its not there
            if not lic:
                lic = License(number=license_number, licensee=provider,
                              licensor=self._nysop)
                """
                It's a requirement of association tables in sqlalchemy that the
                "child" in the relationship must be explicitly associated with
                the association record. see:
                docs.sqlalchemy.org/en/latest/orm/basic_relationships.html
                #association-object
                """
                provider.licenses.append(lic)

        cert_number = m(row, 'certificate_number', str)
        if cert_number:
            q = self._session.query(License) \
                .filter_by(number=cert_number, licensor_id=self._abpn.id)
            cert = q.options(load_only("licensee_id")).one_or_none()

            if not cert:
                cert = License(number=cert_number, licensor=self._abpn,
                               licensee=provider)
                provider.licenses.append(cert)
