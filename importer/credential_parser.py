import sys
from typing import Mapping, Tuple, Set, MutableMapping, List

from fixtures.academic_degrees import ACRONYM_MAP as DEGREE_ACRONYMS
from fixtures.licenses_and_certifications import CREDENTIAL_ACRONYMS

# Do not modify these, or else you break the thread safety!
_CRED_ACRO_MAP: MutableMapping[str, str] = {}
_CRED_FULL_MAP: MutableMapping[str, str] = {}
for acro, name in CREDENTIAL_ACRONYMS.items():
    a_l = acro.lower()
    c_l = name.lower()

    if a_l in DEGREE_ACRONYMS:
        print("cred/degree collision", a_l)
        sys.exit(1)

    _CRED_ACRO_MAP[a_l] = acro
    _CRED_FULL_MAP[c_l] = a_l

""" A list of 2-tuples where CRED[0] _must_ have DEGREE[1] """
CRED_REQ_DEG: Tuple[Tuple[str, str]] = (
    ('faacp', 'phd'),
)


class CredentialParser:
    # @TODO: All of this can be mined for more information
    """ terms that when encountered literally are ignored """
    BLACKLIST: frozenset = frozenset([
        'jr',  # This means Junior
        'sr',  # This means Senior

        # 7 Chars seems max for psychtoday input
        'doctora',
        'candida',
        'license',
        'psychol',
        'interna',
        'mediate',
        'elizabe',
        'psychoa',
        'hypnoth',
        'marriag',
        'therapi',
        'body',
        'mind',
        'life',
        'coach',
        'mentor',
        'dance',
        'family',
        'therapy',
        'speaker',
        'author',
        'prof',
        'staff',
        'cert',
        'clin',
        'hyp',

        # Meaningless ad/buisiness crossed wires
        'dir',  # appears to be a business listing using psychtoday
        'pllc',  # This is a professional llc,
        'llc',  # LLC
        'the possibility practice',  # no
        'counseling services',  # no
        'yoga',  # not what we're filtering for
        'nyu',  # A university
        'ac'  # accupuncture isn't what we're filtering for
    ])

    """ terms that when encountered literally are replaced with one or more 
    others """
    ALIAS_MAP: Mapping[str, Tuple[str]] = {
        'master social worker': ('msw',),
        'master social work': ('msw',),
        'clinical social worker': ('csw',),
        'clinical social work': ('csw',),
        'abpp-cn': ('abpp', 'clinical neuropsychologist'),
        'ms ed': ('msed',),
        'r': ('lcsw-r',),
        '-r': ('lcsw-r',),
        'r-': ('lcsw-r',),
        'iayt': ('c-iayt',),
        'iayt-c': ('c-iayt',),
        'acsw-r': ('acsw',),
        'np-p': ('npp',),
        'psy': ('psyd',),
        'rdmt': ('dmt',),
        'r-dmt': ('dmt',),
        'lcswr': ('lcsw-r',),
        'lcswr ny nj': ('lcsw-r',),
        'lacsw-r': ('lcsw-r',),
        'lcsw - r': ('lcsw-r',),
        'lcsw-pr': ('lcsw-r',),
        'lmswny': ('lmsw',),
        'lmsw-lp': ('lmsw',),
        'osw': ('osw-c',),
        'oswc': ('osw-c',),
        'lcswnj': ('lcsw',),
        'r-lcsw': ('lcsw-r',),
        'lcswc': ('lcsw-c',),
        'lcswcp': ('lcsw-cp',),
        'mft-lp': ('lmft',),
        'lmft-s': ('lmft',),
        'mhc-lp': ('lmhc',),
        '-bc': ('pmhnp',),
        'pmhnp-': ('pmhnp',),
        'csac-t': ('casac-t',),
        'casacg': ('casac-g',),
        'casact': ('casac-t',),
        'lcswacp': ('lcsw-acp',),
        'pmhnp-b': ('pmhnp',),
        'camsi': ('cams-i',),
        'camsii': ('cams-ii',),
        'camsiii': ('cams-iii',),
        'camsiv': ('cams-iv',),
        'camsv': ('cams-v',),
        'cams i': ('cams-i',),
        'cams ii': ('cams-ii',),
        'cams iii': ('cams-iii',),
        'cams iv': ('cams-iv',),
        'cams v': ('cams-v',),
        'ncaci': ('ncac-i',),
        'ncacii': ('ncac-ii',),
        'ncac i': ('ncac-i',),
        'ncac ii': ('ncac-ii',),
        'emdr-i': ('emdr',),  # This is a level of training not a cert
        'bcia-c': ('bcb',),  # This means bcia-certified which is vague

        # The ABECSW issues a BCD, and the ABPsa issues a BCD-P
        # They appear to be the same thing
        'bcd-p': ('bcd',),
    }

    """ Things associated with psuedoscience/antivax/homeopathy etc. """
    WARN: frozenset = frozenset([
        'abihm',
        'rpp',
        'evoker', 'healer',
        'chhc',
        'hhc',
        'holistic psychotherapist',
        'intern',
        'reiki',
        'tbt',  # https://www.ncbi.nlm.nih.gov/pubmed/27301967
    ])

    """
    These are vanity notations which indicates how the provider wants to sell
    themselves to the patient. what do here? this could be one of the early ways
    we chop out the confusion: we shouldn't care how the providers think is best
    to market themselves. it increases confusion
    """
    HONORIFICS: Mapping[str, set] = {
        'psychiatrist': {},
        'psychiatric nurse practitioner': {},
        'counselor': {},  # what certs indicate this/ let people say this?
        'therapist': {},  # Obviously anyone can say this
        'psychologist': {},  # is it true that all have phd?
        'art therapist': {},  # is it always true that they have lcat?
        'creative arts therapist': {},  # always have lcat?
        'licensed psychotherapist': {},  # No credential given
        'psychotherapist': {},
        'certified psychoanalyst': {},
        'licensed clinical psychologist': {},
        'psychiatric nurse': {},  # Is this true? All PNs have an RN?
        'licensed psychoanalyst': {},
        'licensed psychologist': {},
        'clinical neuropsychologist': {},

    }

    """Sometimes they list modalities as credentials"""
    MODALITIES: frozenset = frozenset([
        'emdr',
        'analyst',  # i think this might mean jungian?
        'certified jungian analyst',  # modality, right?
        'cft',  # compassion focused therapy
        'hypnotherapy',
        'act'  # acceptance & commitment therapy
    ])

    """A list of credentials for which saying "BC" is redundant"""
    IMPLICIT_BOARD_CERTIFICATION: frozenset = frozenset([
        'aprn', 'pmhnp', 'md', 'lcat', 'pmhcns', 'rn'
    ])

    """
    This is executed in order before ANYTHING else happens.
    N.B.: NEVER replace a term with blank
    """
    PREFIX_REPLACEMENTS: Tuple[Tuple[str, str]] = (
        # These are DISALLOWED CHARACTERS. Add things here CAREFULLY
        ('.', ''),
        ('(', ''),
        (')', ''),

        # Replace common mistakes
        ('mhc-, lp', 'mhc-lp'),
        ('lcsw-, r', 'lcsw-r'),
        (' ms, ed,', 'msed;'),
        (' ma, ed,', 'maed;'),
        (' ph, d,', ' phd;'),
        (' l, ac,', 'ac;'),
        ('ncac, ii', 'ncac-ii'),
        ('cams, i', 'cams-i'),
        ('cams, ii', 'cams-ii'),
        ('phd ', 'phd;'),
        ('casac, g,', 'casac-g;'),

        # Things that say "and" are hard to correct for
        ('&', 'and'),
        ('private practice', '__PP'),
        ('pre-licensed professional', '__PLP'),
        ('drug and alcohol counselor', '__DAG'),
        ('marriage and family therapist intern', '__MAFTI'),
        ('marriage and family therapist', 'mft'),

        # Split characters
        (',', ';'),
        ('and', ';'),
        ('/', ';'),
    )

    """
    These are special codes that represent things with no category or that need
    special treatment. Hidden by deafult.
    """
    EXTRAS = {
        "__PP": "private practice",
        "__PLP": "pre-licensed professional",
        "__MAFTI": "marriage and family therapist intern",
        "__DAG": "drug and alcohol counselor"
    }

    """
    The valid splitting delim that will not be interpreted as anything else
    """
    LIST_DELIMITER = ';'

    def __init__(self, raw: str, desc: str = ''):
        """
        Parse a credential string by passing it to this function
        :param raw: The credential string, with creds delimited by ';'
        :param desc: An optional description
        """
        # The input string should be stripped and lowered
        self._raw: str = raw.strip().lower()

        # Optionally a description
        self.description: str = desc

        # Valid tokens we weren't able to find
        self.unknown: Set[str] = set()

        # A list of tokens that were blacklisted like "jr."
        self.blacklist: Set[str] = set()

        # Things that may imply bad service
        self.warn: Set[str] = set()

        # Honorifics that aren't a specifically named credential
        self.honorifics: Set[str] = set()

        # Modalities that were included in the credentials string
        self.modalities: Set[str] = set()

        # Credentials we know about
        self.valid_credentials: Set[str] = set()

        # Degrees we know about
        self.valid_degrees: Set[str] = set()

        # Things that cant be categorized
        self.extras: Set[str] = set()

        # Licensed Psychoanalyst / Licensed Psychologist
        self.lp_credential: bool = False

        # This doesn't appear to mean anything. Is it LCSW?
        self.csw_credential: bool = False

        # Certified / Clinical Psychologist
        self.cp_credential: bool = False

        # Certified Sex Addiction / Substance Abuse Therapist
        self.csat_credential: bool = False

        # Psychologist Associate / Psychoanalyst
        self.psya_credential: bool = False

        # Do they list BC without a clear meaning
        self.ambiguous_board_certification: bool = False

        # Run the parser
        self._process()

    def deduplicate(self, other: 'CredentialParser') -> bool:
        if other.valid_degrees.intersection(self.valid_degrees):
            return True
        if other.valid_credentials.intersection(self.valid_credentials):
            return True
        if other.extras.intersection(self.extras):
            return True
        if other.unknown.intersection(self.unknown):
            return True
        if other.lp_credential == self.lp_credential:
            return True
        if other.csw_credential == self.csw_credential:
            return True
        if other.cp_credential == self.cp_credential:
            return True
        if other.psya_credential == self.psya_credential:
            return True

        return False

    def _process(self) -> None:
        # Do the replacements first
        for args in self.PREFIX_REPLACEMENTS:
            self._raw = self._raw.replace(*args)

        # Now split the string and get the valid creds
        valid: Set[str] = self._split_raw()

        # Now bucketize the tokens we know are valid
        self._parse_valid_tokens(valid)

        # Calculate anything that need be inferred from completed processing
        self._post_process()

    def _split_raw(self) -> Set[str]:
        """
        Take a raw credentials string and split it into sets to be processed
        later. This string is assumed to be unmodified from user entry
        :return: A set containing the known valid tokens
        """
        # Split the string on the known delim first
        tokens = self._raw.split(self.LIST_DELIMITER)

        # Remove things known to be bad
        filtered: Set[str] = set()
        for element in tokens:
            stripped: str = element.strip()

            # Blank lines
            if not stripped:
                continue

            # Since this step can yield valid results with spaces, add it
            if stripped in self.ALIAS_MAP:
                filtered.update(self.ALIAS_MAP[stripped])
                continue

            filtered.add(stripped)

        # Now bucketize the tokens
        pruned: Set[str] = set()
        for element in filtered:
            # We need to filter anything that can legitimately have spaces here
            if element in self.BLACKLIST:
                self.blacklist.add(stripped)
                continue
            if element in self.WARN:
                self.warn.add(stripped)
                continue
            if element in self.HONORIFICS:
                self.honorifics.add(stripped)
                continue
            if element in self.MODALITIES:
                self.modalities.add(stripped)
                continue
            if element in _CRED_FULL_MAP:
                pruned.add(_CRED_FULL_MAP[element])
                continue

            # At this point all spaces get exploded into acronyms
            pruned.update([x.strip() for x in element.split(' ')])

        return pruned

    def _parse_valid_tokens(self, valid_tokens: Set[str]) -> None:
        """
        Tokens that haven't been blacklisted or known to be non-credentials
        are passed to this function to be sorted into buckets
        :param valid_tokens: The list of valid tokens
        """
        for sub in valid_tokens:
            if sub == 'bc':
                self.ambiguous_board_certification = True
                continue

            # We decided to coerce this one!
            if sub == 'csw':
                self.valid_credentials.add("lcsw")
                continue

            if sub in DEGREE_ACRONYMS:
                self.valid_degrees.add(sub)
                continue

            if sub in _CRED_ACRO_MAP:
                self.valid_credentials.add(sub)
                continue

            if sub == 'cp':
                self.cp_credential = True
                continue

            if sub == 'psya':
                self.psya_credential = True
                continue

            # These three are a problem so we have to search again later
            if sub == 'lp':
                self.lp_credential = True
                continue

            # This overlap is hideous
            if sub == 'csat':
                self.csat_credential = True
                continue

            # Special case because this is the one thing i want to track that
            # legitimately has "and" in it
            if sub == "__DAG":
                self.honorifics.add(self.EXTRAS[sub])
                continue

            if sub in self.EXTRAS:
                self.extras.add(self.EXTRAS[sub])
                continue

            # If we got here we should mark this as unknown
            self.unknown.add(sub)

    def _post_process(self) -> None:
        """
        Do anything further processing that requires everything to be fully
        parsed beforehand.
        """
        if self.ambiguous_board_certification:
            # If the intersection of these two sets is not the null set
            # then we can safely assume that BC applies to one of the valid
            # credentials and is thus redundant
            if len(self.valid_credentials & self.IMPLICIT_BOARD_CERTIFICATION):
                self.ambiguous_board_certification = False

    def __str__(self) -> str:
        if self.description:
            return self.description
        else:
            return ' '.join(self.valid_degrees) + ' '.join(
                self.valid_credentials)


def print_cred_stats(creds: List[CredentialParser]) -> None:
    """
    For a set of credentials, print stats on all of them
    :param creds: A list of credentials to statify
    """

    uk = {}

    # Print warnings
    print("=== Credentials Warnings")
    for cred in creds:
        if cred.ambiguous_board_certification:
            print("! ABC", cred)
        for a, b in CRED_REQ_DEG:
            if a in cred.valid_credentials and b not in cred.valid_degrees:
                print("! REQ ({}, {}) {}".format(a, b, cred))
        for elt in cred.warn:
            print('! XXX', elt, cred)
        for u in cred.unknown:
            if u not in uk:
                uk[u] = [cred]
            else:
                uk[u].append(cred)

    single = []

    print()
    print("=== Multiple Unknown Credentials")
    for unknown, creds in uk.items():
        count = len(creds)
        if count < 2:
            single.append((unknown, creds[0]))
            continue
        print(unknown, count)
        for cred in creds:
            print(cred)
        print()

    print()
    print("=== Single Unknown Credentials")
    for unknown, cred in single:
        print("{:10} {}".format(unknown, cred))
