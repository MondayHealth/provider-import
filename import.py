import csv
import os
import re
from typing import List, Tuple, Callable, Mapping

import usaddress

BASE_PATH: str = '/Users/ixtli/Downloads/monday'

FILE_EXT: str = 'csv'


def _de_camel(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def _process_directories(reader: csv.DictReader) -> None:
    name_max: int = 0
    short_name_max: int = 0
    for row in reader:
        name_max = max(len(row['name']), name_max)
        short_name_max = max(len(row['short_name']), short_name_max)
    print("name max", name_max)
    print("short_name max", short_name_max)


def _process_payors(reader: csv.DictReader) -> None:
    name_max: int = 0
    for row in reader:
        name_max = max(len(row['name']), name_max)
    print("name max", name_max)


def _process_locations(reader: csv.DictReader) -> None:
    parts = {}
    types = set()
    failures = []
    for row in reader:
        try:
            tag, address_type = usaddress.tag(row['address'])
        except usaddress.RepeatedLabelError as e:
            failures.append((row['address'], e.MESSAGE))
            continue

        types.add(address_type)
        for key, val in tag.items():
            dc_key = _de_camel(key)
            if dc_key not in parts:
                parts[dc_key] = len(val)
            else:
                parts[dc_key] = max(len(val), parts[dc_key])

    for key, val in parts.items():
        print(key, " - ", val)

    print("address types:", types)

    print(failures)


def _process_plans(reader: csv.DictReader) -> None:
    og_code_max: int = 0
    for row in reader:
        og_code_max = max(len(row['original_code']), og_code_max)
    print("name max", og_code_max)


def _process_providers(reader: csv.DictReader) -> None:
    pass


HANDLERS: Mapping[str, Callable[[csv.DictReader], None]] = {
    "directories": _process_directories,
    "payors": _process_payors,
    # "locations": _process_locations,
    "plans": _process_plans,
    "provider_records": _process_providers,
}


def _discover_files() -> List[Tuple[str, str]]:
    ret = []
    for root, dirs, files in os.walk(BASE_PATH):
        for file in files:
            name = file.split('.')[0]
            path = os.path.join(root, file)
            ret.append((name, path))
    return ret


def _process_file(name: str, reader: csv.DictReader) -> None:
    if name in HANDLERS:
        print("===", name)
        HANDLERS[name](reader)
        print()


def run_from_command_line() -> None:
    for name, path in _discover_files():
        with open(path, newline='') as file:
            reader = csv.DictReader(file)
            _process_file(name, reader)


if __name__ == "__main__":
    run_from_command_line()
