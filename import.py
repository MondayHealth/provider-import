import csv
import os
from collections import OrderedDict
from typing import List, Tuple

import sqlalchemy

BASE_PATH: str = '/Users/ixtli/Downloads/monday'

FILE_EXT: str = 'csv'

FIELD_TYPES: dict = {
    "id": "PRIMARY KEY",
    "record_limit": "int",
    "alias_id": "~UNKNOWN~",
    "certified": "bool",
    "sliding_scale": "bool",
    "free_consultation": "bool",
    "accepting_new_patients": "bool"
}

SUFFIX_TYPES: dict = {
    "at": "date",
    "id": "FOREIGN KEY",
    "number": "int",
    "fee": "int"
}

PREFIX_TYPES: dict = {
    "is": "bool"
}


def discover_files() -> List[Tuple[str, str]]:
    ret = []
    for root, dirs, files in os.walk(BASE_PATH):
        for file in files:
            name = file.split('.')[0]
            path = os.path.join(root, file)
            ret.append((name, path))
    return ret


def get_table_for_column_names(names: List[str]) -> OrderedDict:
    table = OrderedDict()
    for name in names:
        if name in FIELD_TYPES:
            table[name] = FIELD_TYPES[name]
            continue

        tokens = name.split("_")
        last = tokens[-1]

        if last in SUFFIX_TYPES:
            table[name] = SUFFIX_TYPES[last]
            continue

        first = tokens[0]

        if first in PREFIX_TYPES:
            table[name] = PREFIX_TYPES[first]
            continue

        print(name)

        table[name] = "str"

    return table


def run_from_command_line() -> None:
    tables = {}
    for name, path in discover_files():
        with open(path, newline='') as file:
            reader = csv.DictReader(file)
            table = get_table_for_column_names(reader.fieldnames)
            tables[name] = table

    for table, fields in tables.items():
        print(table, fields)


if __name__ == "__main__":
    run_from_command_line()
