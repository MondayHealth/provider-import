from importer.loader import CSVLoader
from importer.munger import Munger


def run_from_command_line() -> None:
    base_path: str = '/Users/ixtli/Downloads/monday'
    loader: CSVLoader = CSVLoader(base_path)
    loader.load()
    munger: Munger = Munger()
    munger.update_fixtures()
    # Initial provider import
    # munger.load_providers(loader.get_tables())

    # Load credentials
    # munger.process_credentials_in_place(loader.get_tables())

    # Load payment methods
    munger.process_payment_methods_in_place(loader.get_tables())
    munger.clean()


if __name__ == "__main__":
    run_from_command_line()
