from typing import List, MutableMapping

import progressbar
from sqlalchemy.orm import Session, load_only, subqueryload

from importer.credential_parser import CredentialParser, print_cred_stats
from importer.loader import RawTable
from importer.provider_munger import ProviderMunger
from importer.util import m
from provider.models.credential import Credential
from provider.models.degree import Degree
from provider.models.license import License
from provider.models.licensor import Licensor
from provider.models.providers import Provider


class CredentialsMunger:
    def __init__(self, session: Session):
        self._session: Session = session
        self._credentials: List[CredentialParser] = []
        self._degree_map: MutableMapping[str, Degree] = {}
        self._credential_map: MutableMapping[str, Credential] = {}
        self._nysop: Licensor = None
        self._generate_maps()

    def _generate_maps(self):
        self._nysop = self._session.query(Licensor).filter_by(
            name=ProviderMunger.NYSOP_NAME).one_or_none()

        for record in self._session.query(Degree).all():
            self._degree_map[record.acronym.lower()] = record

        for record in self._session.query(Credential).all():
            self._credential_map[record.acronym.lower()] = record

    def process(self, table: RawTable) -> None:
        columns, rows = table.get_table_components()

        bar = progressbar.ProgressBar(max_value=len(rows))
        i = 0
        for row in rows:

            license_number = m(row, 'license_number', str)
            row_id = m(row, 'id', int)

            # Try to find a license number
            if license_number:
                q = self._session.query(License)
                q = q.filter_by(number=license_number,
                                licensor_id=self._nysop.id)
                lic = q.options(load_only("licensee_id")).one_or_none()
                if lic:
                    row_id = lic.licensee_id

            q = self._session.query(Provider)
            provider = q.filter_by(id=row_id).options(
                load_only("id"),
                subqueryload("degrees")
            ).one_or_none()

            if not provider:
                print("Couldn't find provider by id", row_id)
                continue

            # Parse out the cred string
            first_name = m(row, 'first_name', str)
            last_name = m(row, 'last_name', str)
            cred_string = m(row, 'license', str)
            d = "{:<30} {}".format(first_name + " " + last_name, cred_string)
            creds = CredentialParser(row['license'], d)
            self._credentials.append(creds)

            for degree in creds.valid_degrees:
                if degree in self._degree_map:
                    provider.degrees.append(self._degree_map[degree])
                else:
                    print('WARNING: No degree record for', degree)

            for cred in creds.valid_credentials:
                if cred in self._credential_map:
                    provider.credentials.append(self._credential_map[cred])
                else:
                    print('WARNING: no cred record for', cred)

            bar.update(i)
            i = i + 1

    def print_skipped(self):
        print_cred_stats(self._credentials)
