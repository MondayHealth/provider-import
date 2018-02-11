from typing import IO, List, Set

import progressbar
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

    def dump(self, file: IO) -> None:
        row_count = self._session.query(func.count(Provider.id)).scalar()
        query = self._session.query(Provider)
        pbar = progressbar.ProgressBar(max_value=row_count, initial_value=0)
        i = 0

        fmt: List[str] = []
        columns: List[str] = []
        for column_name in Provider.__table__.columns.keys():
            if column_name not in self.NO_DUMP:
                columns.append(column_name)
                fmt.append("{" + column_name + "}")

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

        format_string = ",".join(fmt)
        providers: List[Provider] = query.all()
        for provider in providers:
            out: str = format_string.format(**provider.__dict__)
            out = out.replace("None", "")

            accumulator: List = []
            for elt in provider.degrees:
                accumulator.append(elt.acronym)
            sub_out = ";".join(accumulator)
            if sub_out:
                out += "," + sub_out

            accumulator: List = []
            for elt in provider.credentials:
                accumulator.append(elt.acronym)
            sub_out = ";".join(accumulator)
            if sub_out:
                out += "," + sub_out

            accumulator = []
            for elt in provider.directories:
                accumulator.append(str(elt.id))
            sub_out = ";".join(accumulator)
            if sub_out:
                out += "," + sub_out

            accumulator = []
            for elt in provider.groups:
                accumulator.append(elt.body)
            sub_out = ";".join(accumulator)
            if sub_out:
                out += "," + sub_out

            accumulator = []
            for elt in provider.languages:
                accumulator.append(elt.name)
            sub_out = ";".join(accumulator)
            if sub_out:
                out += "," + sub_out

            accumulator = []
            for elt in provider.licenses:
                accumulator.append(elt.number)
            sub_out = ";".join(accumulator)
            if sub_out:
                out += "," + sub_out

            accumulator = []
            for elt in provider.modalities:
                accumulator.append(elt.name)
            sub_out = ";".join(accumulator)
            if sub_out:
                out += "," + sub_out

            accumulator = []
            for elt in provider.treatment_orientations:
                accumulator.append(elt.body)
            sub_out = ";".join(accumulator)
            if sub_out:
                out += "," + sub_out

            accumulator = []
            for elt in provider.specialties:
                accumulator.append(elt.name)
            sub_out = ";".join(accumulator)
            if sub_out:
                out += "," + sub_out

            accumulator = []
            s_acc = set()
            for elt in provider.plans_accepted:
                accumulator.append(str(elt.id))
                s_acc.add(str(elt.payor_id))
            sub_out = ";".join(accumulator)
            if sub_out:
                out += "," + sub_out
            sub_out = ";".join(s_acc)
            if sub_out:
                out += "," + sub_out

            accumulator = []
            for elt in provider.accepted_payor_comments:
                accumulator.append(elt.body)
            sub_out = ";".join(accumulator)
            if sub_out:
                out += "," + sub_out

            accumulator = []
            s_acc = set()
            for elt in provider.addresses:
                if elt.formatted:
                    accumulator.append(elt.formatted)
                    s_acc.add(str(elt.zip_code).zfill(5))
            sub_out = ";".join(s_acc)
            if sub_out:
                out += "," + sub_out
            sub_out = ";".join(accumulator)
            if sub_out:
                out += "," + sub_out

            accumulator = []
            for elt in provider.phone_numbers:
                accumulator.append(str(elt.npa) + str(elt.nxx) + str(elt.xxxx))
            sub_out = ";".join(accumulator)
            if sub_out:
                out += "," + sub_out

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
