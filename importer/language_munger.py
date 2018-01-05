from collections import OrderedDict
from typing import MutableMapping, Set

from sqlalchemy.orm import Session

from importer.munger_plugin_base import MungerPlugin
from importer.util import m
from provider.models.language import Language
from provider.models.providers import Provider


class LanguageMunger(MungerPlugin):
    _PRELOAD = {"eng", "fra", "spa", "deu", "zho"}

    _QUALIFIER_BLACKLIST = [
        'some',
        'limited',
        'basic',
        'minimal',
        'not fluent',
        'elementary',
        'moderate',
        'learning',
        'a bit',
        'working knowledge',
        'n/a',
        'understand'
    ]

    _REPLACE = {
        "hiindi": "hindi",
        "mandarin": "mandarin chinese",
        "american": "english",  # jfc
        "cantonese": "yue chinese",
        "asl": "american sign language",
        "farsi": "persian",
        "nepali": "nepali (individual language)",
        "greek": "modern greek (1453-)",
        "haitian creole": "haitian",
        "haitian-creole": "haitian",
        "french creole": "cajun french",
        "taiwanese": "",
        "punjabi": "",
        "moldavian": "",
        "swahili": "",
        "brazilian portuguese": "",

    }

    def __init__(self, session: Session, debug: bool):
        super().__init__(session, debug)
        self._unknown: MutableMapping[str, Set[str]] = {}
        self._records: MutableMapping[str, Language] = {}
        self._blacklisted: Set[str] = set()

    def pre_process(self) -> None:
        super().pre_process()
        for record in self._session.query(Language).all():
            if record.iso in self._PRELOAD:
                self._records[record.name] = record
            else:
                self._records[record.name] = None

    def _missed(self, token: str, raw: str) -> None:
        if token in self._unknown:
            self._unknown[token].add(raw)
        else:
            self._unknown[token] = {raw}

    def process_row(self, row: OrderedDict, provider: Provider) -> None:
        raw: str = m(row, 'languages', str)

        if not raw:
            return

        found = {self._records['english']}

        replaced_raw = raw.lower() \
            .replace(" and ", ";") \
            .replace("bilingual", "") \
            .replace("proficient", "") \
            .replace("conversational", "") \
            .replace("(", "") \
            .replace(")", "") \
            .replace("/", ";")

        for token in replaced_raw.split(';'):
            lang_name: str = token.strip()

            if not lang_name:
                continue

            if lang_name in self._blacklisted:
                continue

            if lang_name in self._REPLACE:
                lang_name = self._REPLACE[lang_name]
            else:
                found_blacklisted_qualifier = False
                for qualifier in self._QUALIFIER_BLACKLIST:
                    if lang_name.find(qualifier) > -1:
                        self._blacklisted.add(lang_name)
                        found_blacklisted_qualifier = True
                        break
                if found_blacklisted_qualifier:
                    continue

            if lang_name not in self._records:
                self._missed(lang_name, raw)
                continue

            record = self._records[lang_name]
            if not record:
                record = self._session.query(Language).filter_by(
                    name=lang_name).one_or_none()
                assert record, "couldn't find record name " + lang_name
                self._records[lang_name] = record

            found.add(self._records[lang_name])

        if len(found) < 1:
            return

        already = {x for x in provider.languages}

        for lang in found:
            if lang not in already:
                provider.languages.append(lang)

    def post_process(self) -> None:
        super().post_process()
        if self._debug:
            print()
            print("BLACKLISTED")
            for bl in self._blacklisted:
                print(bl)
            print()
            for key, raws in self._unknown.items():
                print()
                print(key, len(raws))
                for raw in raws:
                    print(raw)
