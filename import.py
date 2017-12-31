from importer.loader import CSVLoader
from importer.munger import Munger


def initial_import(m: Munger, l: CSVLoader) -> None:
    m.load_providers(l.get_tables())


def load_credentials(m: Munger, l: CSVLoader) -> None:
    m.process_credentials_in_place(l.get_tables())


def run_from_command_line() -> None:
    base_path: str = '/Users/ixtli/Downloads/monday'
    loader: CSVLoader = CSVLoader(base_path)
    loader.load()
    munger: Munger = Munger()
    munger.update_fixtures()
    load_credentials(munger, loader)
    munger.clean()


if __name__ == "__main__":
    run_from_command_line()
