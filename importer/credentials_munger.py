from collections import OrderedDict
from typing import List, MutableMapping

from sqlalchemy.orm import load_only

from importer.credential_parser import CredentialParser, print_cred_stats
from importer.munger_plugin_base import MungerPlugin
from importer.util import m
from provider.models.credential import Credential
from provider.models.degree import Degree
from provider.models.modalities import Modality
from provider.models.providers import Provider


class CredentialsMunger(MungerPlugin):
    def __init__(self, *args):
        super().__init__(*args)

        if self._debug:
            self._credentials: List[CredentialParser] = []

        self._degree_map: MutableMapping[str, Degree] = {}
        self._credential_map: MutableMapping[str, Credential] = {}
        self._generate_maps()

    def _generate_maps(self):
        for record in self._session.query(Degree).all():
            self._degree_map[record.acronym.lower()] = record

        for record in self._session.query(Credential).all():
            self._credential_map[record.acronym.lower()] = record

    def process_row(self, row: OrderedDict, provider: Provider) -> None:
        d = None
        if self._debug:
            first_name = m(row, 'first_name', str)
            last_name = m(row, 'last_name', str)
            cred_string = m(row, 'license', str)
            d = "{:<30} {}".format(first_name + " " + last_name, cred_string)

        creds = CredentialParser(row['license'], d)

        if self._debug:
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

        for modality_name in creds.modalities:
            record: Modality = self._session.query(Modality).filter_by(
                name=modality_name).options(load_only('id')).one_or_none()

            if not record:
                record = Modality(name=modality_name)
                self._session.add(record)

            provider.modalities.append(record)

    def post_process(self) -> None:
        super().post_process()
        if self._debug:
            print_cred_stats(self._credentials)
