from dedupe.deduplicator import Deduplicator
from importer.loader import CSVLoader


def run_from_cli():
    base_path: str = '/Users/ixtli/Downloads/monday'
    loader: CSVLoader = CSVLoader(base_path)
    loader.load()
    tables = loader.get_tables()
    d = Deduplicator()
    d.build_index(tables)


if __name__ == "__main__":
    run_from_cli()
