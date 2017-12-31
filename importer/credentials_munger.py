from collections import OrderedDict
from typing import MutableMapping, List, Tuple, Mapping

import progressbar
from sqlalchemy.orm import Session

from importer.academic_degrees import ACRONYM_MAP
from importer.licenses_and_certifications import CREDENTIAL_ACRONYMS
from importer.loader import RawTable


class CredentialsMunger:
    BLACKLIST = {
        'clinical social work/therapist',  # psych today cruft
        'i',  # Probably I
        'ii',  # Probably II
        'iii',  # Probably III
        'iv',  # Probably IV
        'v',  # Probably V
        'jr',  # This means Junior <_<

        # 7 Chars seems max for psychtoday input
        'doctora',
        'candida',
        'license',
        'psychol',
        'interna',
        'mediate',
        'elizabe',
        'psychoa',

        # Crap
        'life',  # no
        'coach',  # no
        'mentor',  # no
        'dance',  # no
        'therapy',  # no
        'speaker',  # no
        'yoga',  # no
        'author',  # no
        'prof',  # no

        # Meaningless ad/buisiness crossed wires
        'dir',  # appears to be a business listing using psychtoday
        'pllc',  # This is a professional llc,
        'llc',  # LLC
        'marriage & family therapist intern',  # no
        'the possibility practice',  # no
        'counseling services',  # no

        # DEEPER LOOK
        'mhs',  # Probably not a credential??
        'bc',  # "board certified", almost always with PMHNP, redundant?
        'cert',  # This seems to just stand for "certified"
        'mhc',  # By itself i dont think this means anything. please examine
        'mmh',  # Four people who are all LMHC have this, no board
        'mhc-lp',  # It's unclear that this is real. Need a licensing body
        'sep',  # Can't figure out what this is. society experimental psych?
        'pc',  # Can't figure out what this is
        'sudp',  # Can't figure out what this is. 5 occurences of "MD, SUDP"
        'pal'  # What does this mean? there are 42 of them and no google matches
    }

    ALIAS_MAP: Mapping[str, Tuple[str]] = {
        'licensed master social worker': ('lmsw',),
        'master social worker': ('msw',),
        'master social work': ('msw',),
        'master of social work': ('msw',),
        'marriage & family therapist': ('mft',),
        'r': ('lcsw-r',),
        '-r': ('lcsw-r',),
        'r-': ('lcsw-r',),
        'np-p': ('npp',),
        'psy': ('psyd',),
        'lcswr': ('lcsw-r',),
        'lcswr (ny) (nj)': ('lcsw-r',),
        'lacsw-r': ('lcsw-r',),
        'lcsw - r': ('lcsw-r',),
        'lmsw(ny': ('lmsw',),
        'lcsw(nj': ('lcsw',),
        'r-lcsw': ('lcsw-r',),
        'lcswc': ('lcsw-c',),
        'lcswcp': ('lcsw-cp',),
        '-bc': ('pmhnp',),
        'pmhnp-': ('pmhnp',),
        'csac-t': ('casac-t',),
        'casac(g': ('casac-g',),
        'casact': ('casac-t',),
        'lcswacp': ('lcsw-acp',),
        'pmhnp-b': ('pmhnp',),
        'dr': ('phd',),
        'ms msw': ('ms', 'msw',),
        'lcsw msw': ('lcsw', 'msw'),
        'hypnoth': ('hypnotherapy',),
        'phd private practice': ('phd',),
        'phd/psychologist': ('phd', 'psychologist'),
        'phd licensed clinical psychologist': (
            'phd', 'licensed clinical psychologist'),

        # The ABECSW issues a BCD, and the ABPsa issues a BCD-P
        # They appear to be the same thing
        'bcd-p': ('bcd',),
    }

    # Things associated with psuedoscience/antivax/homeopathy etc.
    # We need to talk about this
    WARN = {'abihm', 'rpp', 'evoker', 'healer', 'chhc', 'hhc',
            'holistic psychotherapist', 'intern', 'reiki'}

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
        'psychotherapist': {},
        'certified psychoanalyst': {},
        'licensed clinical psychologist': {'phd'},
        'psychiatric nurse': {'rn'}  # Is this true? All PNs have an RN?
    }

    CRED_DEGREE_REQS = {
        'faacp': 'phd'
    }

    # Sometimes they list modalities as credentials?
    MODALITIES = {
        'emdr',
        'analyst',  # i think this might mean jungian?
        'certified jungian analyst',  # modality, right?
        'cft',  # compassion focused therapy
        'hypnotherapy',
        'act'  # acceptance & commitment therapy
    }

    PREFIX_REPLACEMENTS = (
        (' ph, d,', ' phd;'),
        ('casac, g,', 'casac-g;'),
        (',', ';'),
        ('and', ';'),
        ('.', '')
    )

    def __init__(self, session: Session):
        self._session: Session = session
        self._skipped: MutableMapping[str, List[OrderedDict]] = {}

    def _skip(self, row: OrderedDict, raw: str) -> None:
        if raw not in self._skipped:
            self._skipped[raw] = [row]
        else:
            self._skipped[raw].append(row)

    def _blacklist_split(self, raw: str) -> List:

        replaced_raw = raw
        for args in self.PREFIX_REPLACEMENTS:
            replaced_raw = replaced_raw.replace(*args)

        ret: List = []

        for element in replaced_raw.strip().split(';'):
            stripped: str = element.strip()

            # Blank lines
            if not stripped:
                continue

            # Ignore anything directly matching the blacklist
            if stripped in self.BLACKLIST:
                continue

            # Replace anything directly matching the mistype list
            if stripped in self.ALIAS_MAP:
                ret += list(self.ALIAS_MAP[stripped])
            else:
                # Else, split the line normally
                ret.append(stripped)

        return ret

    def process(self, table: RawTable) -> None:
        columns, rows = table.get_table_components()

        bar = progressbar.ProgressBar(max_value=len(rows))
        i = 0

        cred_map = {}
        cred_full_map = {}
        for acro, name in CREDENTIAL_ACRONYMS.items():
            a_l = acro.lower()
            c_l = name.lower()

            if a_l in ACRONYM_MAP:
                print("cred/degree collision", a_l)
                return

            cred_map[a_l] = acro
            cred_full_map[c_l] = acro

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

            # Psychologist Associate / Psychoanalyst
            psya_cred = False

            # Only deal in lowercases
            raw = row['license'].lower()

            for sub in self._blacklist_split(raw):

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

                if sub == 'psya':
                    psya_cred = True
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

                self._skip(row, sub)

            for cred, degree in self.CRED_DEGREE_REQS.items():
                if cred in valid_creds and degree not in valid_degrees:
                    print("WARN", cred, "REQUIRES", degree)
                    print(row['first_name'], row['last_name'], row['license'])

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
