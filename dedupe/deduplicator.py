from collections import OrderedDict
from typing import Mapping, MutableMapping, List, Tuple

import progressbar
import redis
from redis import StrictRedis

from importer.loader import RawTable
from importer.util import m


class Deduplicator:
    """ Scan a data source (say, provider_records.xls) and generate a record
    map from its IDs to a unique, incrementing id in Redis. """

    def __init__(self):
        self._r: StrictRedis = redis.StrictRedis()

        self._pid_counter: int = 0

        self._id_pid_map: MutableMapping[int, str] = {}

        self._hash_row_map: MutableMapping[
            str, MutableMapping[str, OrderedDict]] = {}

        self._hash_pid_map: MutableMapping[str, int] = {}
        self._pid_hash_map: MutableMapping[int, str] = {}

        self._license_pid_map: MutableMapping[str, int] = {}
        self._pid_license_map: MutableMapping[int, str] = {}

        self._cert_pid_map: MutableMapping[str, int] = {}
        self._pid_cert_map: MutableMapping[int, str] = {}

        self._failed_rows: List[Tuple[str, str, OrderedDict]] = []
        self._duplicate_hashes: MutableMapping[str, List[OrderedDict]] = {}

    def _throw(self, row: OrderedDict, record_hash: str, msg: str) -> None:
        self._failed_rows.append((record_hash, msg, row))

    def _update_cert_for_hash(self, row: OrderedDict, pid: int,
                              record_hash: str) -> bool:
        cert_number = m(row, 'certificate_number', str)
        if not cert_number:
            return False

        conflict_cert = self._pid_cert_map.get(pid)
        if conflict_cert and conflict_cert != cert_number:
            r_hash = self._pid_hash_map[pid]
            msg = "duplicate license # A: {} {} - B: {} {}"
            msg = msg.format(r_hash, conflict_cert, record_hash, cert_number)
            self._throw(row, r_hash, msg)
            return True

        self._cert_pid_map[cert_number] = pid
        self._pid_cert_map[pid] = cert_number
        return False

    def _update_license_for_hash(self, row: OrderedDict, pid: int,
                                 record_hash: str) -> bool:
        license_number = m(row, 'license_number', str)
        if not license_number:
            return False

        try:
            license_number = str(int(license_number))
        except ValueError:
            pass

        conflict_license = self._pid_license_map.get(pid)
        if conflict_license and conflict_license != license_number:
            r_hash = self._pid_hash_map[pid]
            msg = "duplicate license # A: {} {} - B: {} {}"
            msg = msg.format(r_hash, conflict_license, record_hash,
                             license_number)
            self._throw(row, r_hash, msg)
            return True

        self._license_pid_map[license_number] = pid
        self._pid_license_map[pid] = license_number
        return True

    def build_index(self, tables: Mapping[str, RawTable]) -> None:
        table = tables['provider_records']
        columns, rows = table.get_table_components()

        i = 0
        bar = progressbar.ProgressBar(max_value=len(rows), initial_value=i)

        for row in rows:

            row_id: int = m(row, 'id', int)

            last_name: str = m(row, 'last_name', str, "")

            if not last_name:
                self._throw(row, i, "no last name")

            directory_id: str = m(row, 'directory_id', str, None)

            if not directory_id:
                directory_id = m(row, 'payor_id', str, None)
                if not directory_id:
                    self._throw(row, "XXX", "no directory or payor")
                    continue

            first_name: str = m(row, 'first_name', str, "")
            first_name = "".join(first_name.replace(".", "").split()).lower()
            last_name = "".join(last_name.replace(".", "").split()).lower()

            record_hash = ".".join([first_name, last_name])

            if record_hash in self._hash_row_map:
                # This state shouldn't happen, so record it in order to print
                if directory_id in self._hash_row_map[record_hash]:
                    dup_id = record_hash + "." + directory_id
                    if dup_id in self._duplicate_hashes:
                        self._duplicate_hashes[dup_id].append(row)
                    else:
                        self._duplicate_hashes[dup_id] = [row]
                    continue
                self._hash_row_map[record_hash][directory_id] = row
                continue
            else:
                self._hash_row_map[record_hash] = {directory_id: row}

            if row_id in self._id_pid_map:
                pid = self._id_pid_map[row_id]
            else:
                pid = self._pid_counter
                self._pid_counter += 1

            if self._update_cert_for_hash(row, pid, record_hash):
                continue

            if self._update_license_for_hash(row, pid, record_hash):
                continue

            self._hash_pid_map[record_hash] = pid
            self._pid_hash_map[pid] = record_hash
            self._id_pid_map[row_id] = pid

            i += 1
            bar.update(i)

        print()
        for h, msg, r in self._failed_rows:
            print(msg)
        print()
        for name, rows in self._duplicate_hashes.items():
            for row in rows:
                print(name, "{payor_id};{directory_id}".format(**row))
        print()
        print(len(self._hash_row_map), "records")
        print(len(self._duplicate_hashes), "duplicate hashes")
        print(len(self._failed_rows), "failed rows")
