import csv
import os
from typing import List, Tuple, Callable, Mapping

BASE_PATH: str = '/Users/ixtli/Downloads/monday'

FILE_EXT: str = 'csv'


def _process_directories(reader: csv.DictReader) -> None:
    name_max = 0
    short_name_max = 0
    for row in reader:
        name_max = max(len(row['name']), name_max)
        short_name_max = max(len(row['short_name']), short_name_max)
    print("name max", name_max)
    print("short_name max", short_name_max)


def _process_payors(reader: csv.DictReader) -> None:
    name_max = 0
    for row in reader:
        name_max = max(len(row['name']), name_max)
    print("name max", name_max)


def _process_locations(reader: csv.DictReader) -> None:
    addy_max = 0
    for row in reader:
        addy_max = max(len(row['address']), addy_max)
    print("addy max", addy_max)


HANDLERS: Mapping[str, Callable[[csv.DictReader], None]] = {
    "directories": _process_directories,
    "payors": _process_payors,
    "locations": _process_locations
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
