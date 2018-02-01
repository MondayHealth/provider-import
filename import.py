from clean import DatabaseCleaner
from importer.accepted_payor_munger import AcceptedPayorsMunger
from importer.accepted_plans_munger import AcceptedPlanMunger
from importer.age_range_munger import AgeRangeMunger
from importer.credentials_munger import CredentialsMunger
from importer.groups_munger import GroupsMunger
from importer.language_munger import LanguageMunger
from importer.license_cert_munger import LicenseCertMunger
from importer.loader import CSVLoader
from importer.modalities_munger import ModalityMunger
from importer.munger import Munger
from importer.orientation_munger import OrientationMunger
from importer.payment_munger import PaymentMunger
from importer.phone_addy_munger import PhoneAddyMunger
from importer.specialty_munger import SpecialtyMunger


def run_from_command_line() -> None:
    base_path: str = '/Users/ixtli/Downloads/monday'
    loader: CSVLoader = CSVLoader(base_path)
    loader.load()
    tables = loader.get_tables()

    plugin_debug = True
    update_provider_fields = False

    plugins = (
        LicenseCertMunger,
        PhoneAddyMunger,
        CredentialsMunger,
        PaymentMunger,
        AcceptedPlanMunger,
        SpecialtyMunger,
        LanguageMunger,
        OrientationMunger,
        GroupsMunger,
        AcceptedPayorsMunger,
        ModalityMunger,
        AgeRangeMunger,
    )

    munger: Munger = Munger(plugins, plugin_debug)
    munger.update_fixtures()
    # Initial provider import
    munger.load_small_tables(tables)
    munger.process_providers(tables, update_provider_fields)
    cleaner = DatabaseCleaner()
    cleaner.clean()


if __name__ == "__main__":
    run_from_command_line()
