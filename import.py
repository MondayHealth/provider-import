from importer.loader import CSVLoader
from importer.munger import Munger


def run_from_command_line() -> None:
    base_path: str = '/Users/ixtli/Downloads/monday'
    loader: CSVLoader = CSVLoader(base_path)
    loader.load()
    munger: Munger = Munger()
    munger.munge(loader.get_tables())


if __name__ == "__main__":
    run_from_command_line()
