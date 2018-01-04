""" Some sources of data are in python files, scan the DB and update these """
import progressbar
from sqlalchemy.orm import Session

from fixtures.academic_degrees import DEGREES, ACRONYM_MAP
from fixtures.licenses_and_certifications import CREDENTIAL_ACRONYMS
from fixtures.specialties import SPECIALTIES
from provider.models.credential import Credential
from provider.models.degree import Degree
from provider.models.payment_methods import PaymentMethodType, PaymentMethod
from provider.models.specialties import Specialty


class FixtureUpdater:
    def __init__(self, session: Session):
        self._session = session

    def _update_payment_methods(self) -> None:
        methods = set([x for x in PaymentMethodType])
        for r in self._session.query(PaymentMethod).all():
            methods.remove(r.payment_type)

        for method in methods:
            pm = PaymentMethod(payment_type=method)
            self._session.add(pm)

    def _update_licences_and_certifications(self) -> None:
        bar = progressbar.ProgressBar(max_value=len(CREDENTIAL_ACRONYMS))
        i = 0
        for acronym, name in CREDENTIAL_ACRONYMS.items():
            args = {'acronym': acronym, 'full_name': name}
            query = self._session.query(Credential).filter_by(**args)
            if not query.one_or_none():
                self._session.add(Credential(**args))
            i += 1
            bar.update(i)

    def _update_degrees(self) -> None:
        bar = progressbar.ProgressBar(max_value=len(ACRONYM_MAP))
        i = 0
        for level, degrees in DEGREES.items():
            for degree, acronyms in degrees.items():
                for acronym in acronyms:
                    args = {'acronym': acronym, 'name': degree, 'level': level}
                    query = self._session.query(Degree).filter_by(**args)
                    if not query.one_or_none():
                        self._session.add(Degree(**args))
                    i += 1
                    bar.update(i)

    def _update_specialties(self) -> None:
        to_put = set(SPECIALTIES)
        for sp in self._session.query(Specialty).all():
            to_put.remove(sp.name)

        for sp_name in to_put:
            self._session.add(Specialty(name=sp_name))

    def run(self) -> None:
        self._update_degrees()
        self._update_licences_and_certifications()
        self._update_payment_methods()
        self._update_specialties()
