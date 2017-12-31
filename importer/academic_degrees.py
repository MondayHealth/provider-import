import sys
from enum import Enum as BuiltinEnum
from enum import auto
from typing import Mapping, Set, MutableMapping


class EducationLevel(BuiltinEnum):
    associate = auto()
    bachelor = auto()
    master = auto()
    doctor = auto()


DEGREES: Mapping[str, Mapping[str, Set[str]]] = {
    EducationLevel.associate: {
        'arts': {'aa'},
        'science': {'as'}
    },
    EducationLevel.bachelor: {
        'arts': {'ba', 'ab', 'barts', },
        'science and arts': {'bsa', },
        'accountancy': {'bacy', },
        'accounting': {'bacc', },
        'animal and veterinary bioscience': {'banvetbiosc', },
        'applied science': {'bappsc', 'basc', },
        'architecture': {'barch', },
        'business administration': {'bba', },
        'civil engineering': {'bce', },
        'communications': {'bcomm', },
        'dental medicine': {'bdm', },
        'dental science': {'bdsc', },
        'dental surgery': {'bds', 'bchd', },
        'dentistry': {'bdent', },
        'design': {'bdes', },
        'design computing': {'bdescomp', },
        'design in architecture': {'bdesarch', },
        'education': {'bed', },
        'engineering': {'beng', 'be', },
        'electronic commerce': {'bec', 'be-com', },
        'electrical engineering': {'bee', },
        'fine arts': {'bfa', },
        'health sciences': {'bhlthsci', },
        'information technology': {'bit', },
        'international and global studies': {'bigs', },
        'law': {'llb', },
        'liberal arts and sciences': {'blas', },
        'library science': {'blib', 'bls', },
        'literature': {'blit', },
        'mathematics': {'bmath', },
        'mechanical engineering': {'bme', },
        'medical science': {'bmedsc', },
        'medicine': {'mb', },
        'music studies': {'bmusstudies', },
        'nursing': {'bn', },
        'pharmacy': {'bpharm', },
        'political, economic and social sciences': {'bpess', },
        'resource economics': {'bresec', },
        'science': {'bs', 'bsc', },
        'science in environmental and occupational health': {'bseoh', },
        'science in nursing': {'bsn', },
        'socio-legal studies': {'bsls', },
        'veterinary science': {'bvsc', },
        'visual arts': {'bva', }
    },
    EducationLevel.master: {
        'arts': {'ma', 'am', },
        'business administration': {'mba', },
        'commerce': {'mcom', },
        'divinity': {'mdiv', },
        'education': {'med', },
        'fine arts': {'mfa', },
        'international affairs': {'mia', },
        'international studies': {'mis', },
        'laws': {'llm', },
        'library science': {'mls', },
        'liberal arts': {'mla', },
        'professional studies': {'mps', },
        'public administration': {'mpa', },
        'public health': {'mph', },
        'science': {'ms', 'msc', },
        'social work': {'msw', },
        'strategic foresight': {'msf', },
        'science in education': {'msed', },
        'science in social work': {'mssw'},
        'theology': {'thm', }
    },
    EducationLevel.doctor: {
        'audiology': {'aud', },
        'chiropractic': {'dc', },
        'dental surgery': {'dds', },
        'divinity': {'dd', },
        'education': {'edd', },
        'medical dentistry': {'dmd', },
        'medicine': {'md', },
        'ministry': {'dmin', },
        'naturopathy': {'nd', },
        'nursing practice': {'dnp', },
        'optometry': {'od', },
        'osteopathy': {'do', },
        'pharmacy': {'pharmd', },
        'philosophy': {'phd', 'dphil', 'dph', },
        'physical therapy': {'dpt', },
        'psychology': {'psyd', },
        'public health': {'drph', },
        'science': {'dsc', 'scd', },
        'theology': {'dth', 'thd', },
        'veterinary medicine': {'dvm', }
    }
}

ACRONYM_MAP: MutableMapping[str, str] = {}

# Construct acronym map
for level, levels in DEGREES.items():
    level_name = str(level).split('.')[1].lower()
    for key, acro_set in levels.items():
        for acro in acro_set:
            if acro in ACRONYM_MAP:
                print("duplicate", acro, key)
                sys.exit(1)
            ACRONYM_MAP[acro] = level_name + " of " + key
