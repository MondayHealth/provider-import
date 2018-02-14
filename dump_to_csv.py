from typing import IO, List, Set

import progressbar
from psycopg2._range import NumericRange
from sqlalchemy import func
from sqlalchemy.orm import Session

from importer.npi_import import NPIImporter
from provider.models.directories import Directory
from provider.models.payors import Payor
from provider.models.plans import Plan
from provider.models.providers import Provider


class CSVDumper:
    NO_DUMP: Set[str] = {"name_tsv", "created_at", "updated_at"}

    def __init__(self):
        self._session: Session = NPIImporter.get_session()

    @staticmethod
    def _str_for_numeric_range(range: NumericRange) -> str:
        a = range._bounds[0]
        b = range._bounds[1]
        return "{}{}-{}{}".format(a, range.lower, range.upper, b)

    def dump(self, file: IO) -> None:
        row_count = self._session.query(func.count(Provider.id)).scalar()
        query = self._session.query(Provider)
        pbar = progressbar.ProgressBar(max_value=row_count, initial_value=0)
        i = 0

        columns: List[str] = []
        dict_keys: List[str] = []
        for column_name in Provider.__table__.columns.keys():
            if column_name not in self.NO_DUMP:
                dict_keys.append(column_name)
                columns.append(column_name)

        columns.append("degrees")
        columns.append("credentials")
        columns.append("directories")
        columns.append("groups")
        columns.append("languages")
        columns.append("licenses")
        columns.append("modalities")
        columns.append("orientations")
        columns.append("specialties")
        columns.append("plans")
        columns.append("payors")
        columns.append("payor_comments")
        columns.append("zips")
        columns.append("addresses")
        columns.append("phones")

        # Write the column name row
        file.write(",".join(columns) + "\n")

        providers: List[Provider] = query.all()
        for provider in providers:
            cols: List[str] = []
            for key in dict_keys:
                val = provider.__dict__[key]

                if key == "age_groups":
                    if not val or len(val) < 1:
                        cols.append("")
                    else:
                        cols.append(";".join(val))
                    continue

                if key == "age_ranges":
                    if not val or len(val) < 1:
                        cols.append("")
                        continue
                    range_out = []
                    for rng in val:
                        range_out.append(self._str_for_numeric_range(rng))
                    cols.append(";".join(range_out))
                    continue

                if val is not None:
                    cols.append(str(val).replace(",", ""))
                else:
                    cols.append("")

            cols.append(";".join([x.acronym for x in provider.degrees]))

            cols.append(";".join([x.acronym for x in provider.credentials]))

            cols.append(";".join(str(x.id) for x in provider.directories))

            cols.append(
                ";".join([x.body.replace(",", "") for x in provider.groups]))

            cols.append(";".join([x.name for x in provider.languages]))

            cols.append(";".join([x.number for x in provider.licenses]))

            cols.append(";".join(
                [x.name.replace(",", "") for x in provider.modalities]))

            cols.append(";".join([x.body.replace(",", "") for x in
                                  provider.treatment_orientations]))

            cols.append(";".join([x.name.replace(",", "") for x in
                                  provider.specialties]))

            accumulator = []
            s_acc = set()
            for elt in provider.plans_accepted:
                accumulator.append(str(elt.id))
                s_acc.add(str(elt.payor_id))
            cols.append(";".join(accumulator))
            cols.append(";".join(s_acc))

            accumulator = []
            for elt in provider.accepted_payor_comments:
                accumulator.append(elt.body.replace(",", ""))
            cols.append(";".join(accumulator))

            accumulator = []
            s_acc = set()
            for elt in provider.addresses:
                if elt.formatted:
                    accumulator.append(elt.formatted.replace(",", ""))
                if elt.zip_code:
                    s_acc.add(str(elt.zip_code).zfill(5))
            cols.append(";".join(s_acc))
            cols.append(";".join(accumulator))

            accumulator = []
            for elt in provider.phone_numbers:
                accumulator.append(str(elt.npa) + str(elt.nxx) + str(elt.xxxx))
            cols.append(";".join(accumulator))

            out: str = ",".join(cols)
            file.write(out + "\n")
            i += 1
            pbar.update(i)

    def write_directories_key(self, file: IO) -> None:
        dirs: List[Directory] = self._session.query(Directory).all()
        file.write("id,name\n")
        for directory in dirs:
            file.write("{},{}\n".format(directory.id, directory.name))

    def write_plans_key(self, file: IO) -> None:
        plans: List[Plan] = self._session.query(Plan).all()
        file.write("id,name\n")
        for plan in plans:
            file.write("{},{}\n".format(plan.id, plan.name))

    def write_payor_key(self, file: IO) -> None:
        payors: List[Payor] = self._session.query(Payor).all()
        file.write("id,name\n")
        for payor in payors:
            file.write("{},{}\n".format(payor.id, payor.name))


def _run_via_command_line():
    c = CSVDumper()
    with open("providers.csv", 'w') as f:
        c.dump(f)
    with open("directories.csv", 'w') as f:
        c.write_directories_key(f)
    with open("plans.csv", 'w') as f:
        c.write_plans_key(f)
    with open("payors.csv", 'w') as f:
        c.write_payor_key(f)


if __name__ == "__main__":
    _run_via_command_line()
