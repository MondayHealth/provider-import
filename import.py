from importer.language_munger import LanguageMunger
from importer.loader import CSVLoader
from importer.munger import Munger


def run_from_command_line() -> None:
    base_path: str = '/Users/ixtli/Downloads/monday'
    loader: CSVLoader = CSVLoader(base_path)
    loader.load()
    tables = loader.get_tables()

    plugins = (
        # PhoneAddyMunger,
        # CredentialsMunger,
        # PaymentMunger,
        # AcceptedPlanMunger,
        # SpecialtyMunger,
        LanguageMunger,
    )

    munger: Munger = Munger(plugins, True)
    munger.update_fixtures()
    # Initial provider import
    munger.load_small_tables(tables)
    munger.process_providers(tables, False)
    munger.clean()


if __name__ == "__main__":
    run_from_command_line()
