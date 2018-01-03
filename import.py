from importer.accepted_plans_munger import AcceptedPlanMunger
from importer.credentials_munger import CredentialsMunger
from importer.loader import CSVLoader
from importer.munger import Munger
from importer.payment_munger import PaymentMunger
from importer.phone_addy_munger import PhoneAddyMunger
from importer.specialty_munger import SpecialtyMunger


def run_from_command_line() -> None:
    base_path: str = '/Users/ixtli/Downloads/monday'
    loader: CSVLoader = CSVLoader(base_path)
    loader.load()
    tables = loader.get_tables()

    plugins = (
        PhoneAddyMunger,
        CredentialsMunger,
        PaymentMunger,
        AcceptedPlanMunger,
        SpecialtyMunger
    )

    munger: Munger = Munger(plugins, True)
    munger.update_fixtures()
    # Initial provider import
    munger.load_small_tables(tables)
    munger.process_providers(tables, True)
    munger.clean()


if __name__ == "__main__":
    run_from_command_line()
