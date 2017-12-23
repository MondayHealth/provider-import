import csv
import os
from collections import OrderedDict
from typing import Mapping, List, Tuple

# noinspection PyPackageRequirements
import progressbar


class RawTable:
    """
    In memory store of a raw table described as a CSV
    """

    def __init__(self, name: str, columns: list):
        self._name = name
        self._columns: tuple = tuple(columns)
        self._column_index: dict = {x: i for i, x in enumerate(self._columns)}
        self._column_count: int = len(self._columns)
        self._rows: List[OrderedDict] = []

    def add(self, row: OrderedDict) -> None:
        assert len(row) == self._column_count, "incompatible row " + str(row)
        self._rows.append(row)

    def get_table_components(self) -> Tuple[tuple, List[OrderedDict]]:
        return self._columns, self._rows

    def column_index_for_name(self, name: str) -> int:
        return self._column_index[name]


def unknown_bar(name: str) -> progressbar.ProgressBar:
    widgets = [
        name, " ",
        progressbar.RotatingMarker(), " ",
        progressbar.Counter(), " ",
        progressbar.Timer()
    ]
    return progressbar.ProgressBar(max_value=progressbar.UnknownLength,
                                   widgets=widgets)


FILES = frozenset([
    "directories",
    "payors",
    "plans",
    #"locations",
    "provider_records",
    #"specialties",
    #"providers_specialties"
])


class CSVLoader:
    """
    Loads a CSV representation of the scraped dbs into memory
    """

    @staticmethod
    def _discover_files(base_path: str) -> List[Tuple[str, str]]:
        ret = []
        for root, dirs, files in os.walk(base_path):
            for file in files:
                name = file.split('.')[0]
                path = os.path.join(root, file)
                ret.append((name, path))
        return ret

    def __init__(self, base_path: str):
        self._base_path: str = base_path
        self._tables: Mapping[str, RawTable] = {}

    def load(self) -> None:
        for name, path in self._discover_files(self._base_path):
            # Ignore anything we're not concerned with
            if name not in FILES:
                print("Skipping file", name)
                continue
            with open(path, newline='') as file:
                reader = csv.DictReader(file)
                raw = RawTable(name, reader.fieldnames)
                i: int = 0
                with unknown_bar(name) as b:
                    for row in reader:
                        raw.add(row)
                        b.update(i)
                        i = i + 1
                self._tables[name] = raw
                # Clear progresssbar

    def get_tables(self) -> Mapping[str, RawTable]:
        return self._tables
