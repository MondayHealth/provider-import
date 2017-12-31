import pprint
from typing import MutableMapping

import progressbar
from sqlalchemy.orm import Session

from importer.loader import RawTable


class CredentialsMunger:
    BLACKLIST = {
        'marriage & family therapist intern',
    }

    AMBIGUOUS = {
        'CAC': 'Certified Addictions Counselor -or- Certified Alcoholism '
               'Counselor',
        'CP': 'Certified Psychologist -or- Clinical Psychologist',
        'CSW': 'Certified Social Worker -or- Clinical Social Worker',
        'LCP': 'Licensed Clinical Psychologist -or- Licensed Counseling '
               'Professional',
        'LP': 'Licensed Psychoanalyst -or- Licensed Psychologist'
    }

    MAP = {
        'licensed master social worker': 'lmsw',
        'master social worker': 'msw',
        'master social work': 'msw',
        'master of social work': 'msw',
        'clinical social work/therapist': 'csw',
        'clinical social worker': 'csw',
        'clinical social work': 'csw',
        'marriage & family therapist': 'mft',
    }

    def __init__(self, session: Session):
        self._session = session

    def process(self, table: RawTable) -> None:
        columns, rows = table.get_table_components()
        licenses = set()

        bar = progressbar.ProgressBar(max_value=len(rows))
        i = 0

        for row in rows:
            for group in row['license'].strip().split(';'):
                v = []
                for sub in group.split(','):
                    sub = sub.strip().lower().replace(".", "").replace("")
                    if not sub:
                        continue
                    if len(sub) == 1:
                        print(row['license'])
                    v.append(sub)
                licenses.update(v)
            bar.update(i)
            i = i + 1

        begins: MutableMapping[str, set] = {}
        one: set = set()
        two: set = set()
        nothing: set = set()
        for s1 in licenses:
            s1_len = len(s1)
            if s1_len < 3:
                if s1_len == 1:
                    one.add(s1)
                elif s1_len == 2:
                    two.add(s1)
                continue
            bag = set()
            for s2 in licenses:
                s2_len = len(s2)
                if s2_len < s1_len:
                    continue
                if s1 == s2:
                    continue
                if s2[:s1_len] == s1:
                    bag.add(s2)
            if len(bag) > 0:
                begins[s1] = bag
            else:
                nothing.add(s1)

        print(" ")
        pprint.pprint(begins)
        print("NOTHING", nothing)
        print("ONE", one)
        print("TWO", two)
