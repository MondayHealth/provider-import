from collections import OrderedDict
from typing import MutableMapping, List

import progressbar
from sqlalchemy.orm import Session

from importer.academic_degrees import ACRONYM_MAP
from importer.licenses_and_certifications import CREDENTIAL_ACRONYMS
from importer.loader import RawTable


class CredentialsMunger:
    BLACKLIST = {
        'marriage & family therapist intern',
        'clinical social work/therapist',  # Can we always say LCSW? 95% have it
        'g',  # What does this mean? Suzanne Quinn
        'd',  # Bad, from "Ph, D" -- seems to be a bad row
        'i',  # Probably I
        'ii',  # Probably II
        'iii',  # Probably III
        'iv',  # Probably IV
        'v',  # Probably V
        'bc',  # "board certified", almost always with PMHNP, redundant?
        'mhc',  # By itself i dont think this means anything. please examine
        'mhc-lp',  # It's unclear that this is real. Need a licensing body
        'sep',  # Can't figure out what this is. society experimental psych?
        'pc',  # Can't figure out what this is
        'jr',  # This means Junior <_<
        'yoga',  # Not a credential
        'mhs',  # Probably not a credential??
        'author',  # no
        'prof',  # probably not?
        'doctora',  # What does this mean in spanish
        'candida',  # What does this mean in spanish
        'license',  # seems like an input error
        'psychol',  # seems like an input error
        'interna',  # seems like an input error
        'mediate',  # input error
        'dance',  # no
        'therapy',  # no
        'speaker',  # no
        'the possibility practice',  # no
        'counseling services',  # no
        'dir',  # appears to be a business listing using psychtoday
        'pllc',  # This is a professional llc,
        'cert',  # This seems to just stand for "certified"
        'pal'  # What does this mean? there are 42 of them and no google matches
    }

    MISTYPE_MAP = {
        'licensed master social worker': 'lmsw',
        'master social worker': 'msw',
        'master social work': 'msw',
        'master of social work': 'msw',
        'marriage & family therapist': 'mft',
        'r': 'lcsw-r',
        '-r': 'lcsw-r',
        'psy': 'psyd',
        'lcswr': 'lcsw-r',
        'lcswr (ny) (nj)': 'lcsw-r',
        'lacsw-r': 'lcsw-r',
        'lcsw - r': 'lcsw-r',
        'lmsw(ny': 'lmsw',
        'lcsw(nj': 'lcsw',
        'r-lcsw': 'lcsw-r',
        'lcswc': 'lcsw-c',
        'lcswcp': 'lcsw-cp',
        'casac(g': 'casac-g',
        'lcswacp': 'lcsw-acp',
        'pmhnp-b': 'pmhnp',
        'phd/psychologist': 'phd',
        'dr': 'phd',
        'phd private practice': 'phd'
    }

    # Things associated with psuedoscience/antivax/homeopathy etc.
    # We need to talk about this
    WARN = {'abihm', 'rpp', 'evoker', 'healer', 'chhc', 'hhc',
            'holistic psychotherapist'}

    # These are vanity notations which indicates how the provider wants to
    # sell themselves to the patient. what do here? this could be one of the
    # early ways we chop out the confusion: we shouldn't care how the providers
    # think is best to market themselves. it increases confusion
    LICENCES = {
        'psychiatrist': {'md'},
        'psychiatric nurse practitioner': {'PMHNP'},
        'counselor': {},  # what certs indicate this/ let people say this?
        'psychologist': {'phd'},  # is it true that all have phd?
        'art therapist': {'lcat'},  # is it always true that they have lcat?
        'creative arts therapist': {'lcat'},  # always have lcat?
        'drug & alcohol counselor': {'casac', 'ldac'},  # is this it?
        'licensed psychotherapist': {},  # No credential given
        'psychiatric nurse': {'rn'}  # Is this true? All PNs have an RN?
    }

    # Sometimes they list modalities as credentials?
    MODALITIES = {
        'emdr',
        'analyst',  # i think this might mean jungian?
        'certified jungian analyst',  # modality, right?
        'cft',  # compassion focused therapy
        'act'  # acceptance & commitment therapy
    }

    def __init__(self, session: Session):
        self._session: Session = session
        self._skipped: MutableMapping[str, List[OrderedDict]] = {}

    def _skip(self, row: OrderedDict, raw: str) -> None:
        if raw not in self._skipped:
            self._skipped[raw] = [row]
        else:
            self._skipped[raw].append(row)

    def process(self, table: RawTable) -> None:
        columns, rows = table.get_table_components()

        bar = progressbar.ProgressBar(max_value=len(rows))
        i = 0

        cred_map = {}
        cred_full_map = {}
        for acro, name in CREDENTIAL_ACRONYMS.items():
            a_l = acro.lower()
            c_l = name.lower()
            cred_map[a_l] = acro
            cred_full_map[c_l] = acro

        blacklisted = []

        for row in rows:

            valid_creds = set()
            valid_degrees = set()

            licenses = set()

            # Licensed Psychoanalyst / Licensed Psychologist
            lp_creds = set()

            # Modalities
            modalities = set()

            # This means you're trying to get your MHC license but not done
            pre_licence = False

            # This doesn't appear to mean anything. Is it LCSW?
            csw_cred = False

            # Certified / Clinical Psychologist
            cp_cred = False

            # Certified Sex Addiction / Substance Abuse Therapist
            csat_cred = False

            for group in row['license'].lower().strip().split(';'):
                for sub in group.split(','):
                    sub = sub.strip().replace(".", "")
                    if not sub:
                        continue

                    if sub in self.BLACKLIST:
                        blacklisted.append(row['license'])
                        continue
                    if sub in self.MISTYPE_MAP:
                        sub = self.MISTYPE_MAP[sub]

                    if sub in ACRONYM_MAP:
                        valid_degrees.add(sub)
                        continue

                    if sub in cred_map:
                        valid_creds.add(sub)
                        continue

                    if sub in cred_full_map:
                        valid_creds.add(cred_full_map[sub])
                        continue

                    if sub in self.LICENCES:
                        licenses.add(sub)
                        continue

                    if sub in self.MODALITIES:
                        modalities.add(sub)
                        continue

                    if sub == 'csw':
                        csw_cred = True
                        continue

                    if sub == 'cp':
                        cp_cred = True
                        continue

                    # These three are a problem so we have to search again later
                    if sub == 'lp':
                        lp_creds.add(sub)
                        continue
                    if sub == 'licensed psychoanalyst':
                        lp_creds.add(sub)
                        continue
                    if sub == 'licensed psychologist':
                        lp_creds.add(sub)
                        continue

                    # This overlap is hideous
                    if sub == 'csat':
                        csat_cred = True
                        continue

                    if sub == 'pre-licensed professional':
                        pre_licence = True
                        continue

                    if sub in self.WARN:
                        print('WARN', row['first_name'], row['last_name'], sub)
                        continue

                    # This appears to be a typical input error
                    if sub == 'lcsw msw':
                        valid_creds.add('lcsw')
                        valid_degrees.add('msw')
                        continue

                    self._skip(row, sub)

            bar.update(i)
            i = i + 1

        ones = []
        for key, value in self._skipped.items():
            if len(value) < 2:
                ones.append((key, value))
                continue
            print(key, len(value))
            for row in value:
                print(row['first_name'], row['last_name'], row['license'])
            print()

        print()
        for key, value in ones:
            row = value[0]
            print(key, '\t\t\t', row['first_name'], row['last_name'],
                  row['license'])
