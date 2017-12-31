import sys
from enum import Enum as BuiltinEnum
from enum import auto
from typing import Mapping, Set, MutableMapping, Tuple


class EducationLevel(BuiltinEnum):
    associate = auto()
    bachelor = auto()
    master = auto()
    doctor = auto()


DEGREES: Mapping[str, Mapping[str, Set[str]]] = {
    EducationLevel.associate: {
        'Arts': frozenset(['AA', ]),
        'Science': frozenset(['AS', ])
    },
    EducationLevel.bachelor: {
        'Arts': frozenset(['BA', 'AB', 'BArts', ]),
        'Science And Arts': frozenset(['BSA', ]),
        'Accountancy': frozenset(['BAcy', ]),
        'Accounting': frozenset(['BAcc', ]),
        'Animal and Veterinary Bioscience': frozenset(['BAnVetBioSc', ]),
        'Applied Science': frozenset(['BAppSc', 'BASc', ]),
        'Architecture': frozenset(['BArch', ]),
        'Business Administration': frozenset(['BBA', ]),
        'Civil Engineering': frozenset(['BCE', ]),
        'Commerce': frozenset(['BCom', ]),
        'Communications': frozenset(['BComm', ]),
        'Dental Medicine': frozenset(['BDM', ]),
        'Dental Science': frozenset(['BDSc', ]),
        'Dental Surgery': frozenset(['BDS', 'BChD', ]),
        'Dentistry': frozenset(['BDent', ]),
        'Design': frozenset(['BDes', ]),
        'Design Computing': frozenset(['BDesComp', ]),
        'Design in Architecture': frozenset(['BDesArch', ]),
        'Education': frozenset(['BEd', ]),
        'Engineering': frozenset(['BEng', 'BE', ]),
        'Electronic Commerce': frozenset(['BEC', 'BE-COM', ]),
        'Electrical Engineering': frozenset(['BEE', ]),
        'Fine Arts': frozenset(['BFA', ]),
        'Health Sciences': frozenset(['BHlthSci', ]),
        'Information Technology': frozenset(['BIT', ]),
        'International and Global Studies': frozenset(['BIGS', ]),
        'Law': frozenset(['LLB', ]),
        'Liberal Arts and Sciences': frozenset(['BLAS', ]),
        'Library Science': frozenset(['BLib', 'BLS', ]),
        'Literature': frozenset(['BLit', ]),
        'Mathematics': frozenset(['BMath', ]),
        'Mechanical Engineering': frozenset(['BME', ]),
        'Medical Science': frozenset(['BMedSc', ]),
        'Medicine': frozenset(['MB', ]),
        'Music Studies': frozenset(['BMusStudies', ]),
        'Nursing': frozenset(['BN', ]),
        'Pharmacy': frozenset(['BPharm', ]),
        'Political, Economic and Social Sciences': frozenset(['BPESS', ]),
        'Resource Economics': frozenset(['BResEc', ]),
        'Science': frozenset(['BSc', ]),
        'Science in Environmental and Occupational Health': frozenset(
            ['BSEOH', ]),
        'Science in Nursing': frozenset(['BSN', ]),
        'Socio-Legal Studies': frozenset(['BSLS', ]),
        'Veterinary Science': frozenset(['BVSc', ]),
        'Medicine-Bachelor of Surgery': frozenset(['MBBS', ]),
        'Visual Arts': frozenset(['BVA', ]),
    },
    EducationLevel.master: {
        'Arts': frozenset(['MA', 'AM', ]),
        'Arts in Teaching': frozenset(['MAT', ]),
        'Business Administration': frozenset(['MBA', ]),
        'Commerce': frozenset(['MCom', ]),
        'Divinity': frozenset(['MDiv', ]),
        'Education': frozenset(['MEd', 'EdM', ]),
        'Fine Arts': frozenset(['MFA', ]),
        'International Affairs': frozenset(['MIA', ]),
        'International Studies': frozenset(['MIS', ]),
        'Laws': frozenset(['LLM', ]),
        'Library Science': frozenset(['MLS', ]),
        'Liberal Arts': frozenset(['MLA', ]),
        'Professional Studies': frozenset(['MPS', ]),
        'Public Administration': frozenset(['MPA', ]),
        'Science in Nursing': frozenset(['MSN', ]),
        'Science in Education': frozenset(['MSEd', ]),
        'Public Health': frozenset(['MPH', ]),
        'Science': frozenset(['MS', 'MSc', ]),
        'Counseling': frozenset(['MC', ]),
        'Social Work': frozenset(['MSW', ]),
        'Science in Social Work': frozenset(['MSSW', ]),
        'Science in Social Administration': frozenset(['MSSA', ]),
        'Strategic Foresight': frozenset(['MSF', ]),
        'Theology': frozenset(['ThM', ]),
        'Philosophy': frozenset(['MPhil', ]),
    },
    EducationLevel.doctor: {
        'Audiology': frozenset(['AuD', ]),
        'Chiropractic': frozenset(['DC', ]),
        'Dental Surgery': frozenset(['DDS', ]),
        'Divinity': frozenset(['DD', ]),
        'Education': frozenset(['EdD', ]),
        'Jurisprudence': frozenset(['JD', ]),
        'Medical Dentistry': frozenset(['DMD', ]),
        'Medicine': frozenset(['MD', ]),
        'Ministry': frozenset(['DMin', ]),
        'Nursing Practice': frozenset(['DNP', ]),
        'Optometry': frozenset(['OD', ]),
        'Osteopathy': frozenset(['DO', ]),
        'Pharmacy': frozenset(['PharmD', ]),
        'Philosophy': frozenset(['PhD', 'DPhil', 'DPh', ]),
        'Physical Therapy': frozenset(['DPT', ]),
        'Psychology': frozenset(['PsyD', ]),
        'Public Health': frozenset(['DrPH', ]),
        'Social Work': frozenset(['DSW', ]),
        'Science': frozenset(['DSc', 'ScD', ]),
        'Theology': frozenset(['DTh', 'ThD', ]),
        'Letters': frozenset(['DLitt', ]),
        'Veterinary Medicine': frozenset(['DVM', ]),
    }
}

ACRONYM_MAP: MutableMapping[str, Tuple[EducationLevel, str, str]] = {}

# Construct acronym map
for level, levels in DEGREES.items():
    for key, acro_set in levels.items():
        for acro in acro_set:
            a_k_n = acro.lower()
            if a_k_n in ACRONYM_MAP:
                print("duplicate", a_k_n, key)
                sys.exit(1)
            ACRONYM_MAP[a_k_n] = (level, acro, key)
