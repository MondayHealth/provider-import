from dedupe.deduplicator import Deduplicator
from importer.loader import CSVLoader


def run_from_cli():
    base_path: str = '/Users/ixtli/Downloads/monday'
    loader: CSVLoader = CSVLoader(base_path)
    loader.load()
    tables = loader.get_tables()
    d = Deduplicator()

    # This really only needs to be done once unless you changes monday.address
    # d.build_zip_map()

    d.build_index(tables)

    # Sometimes this is a good way to look at what you're doing
    # d.csv()

    # If you just want to look at the results and not change them, comment this
    d.update_map_destructively()


if __name__ == "__main__":
    run_from_cli()
