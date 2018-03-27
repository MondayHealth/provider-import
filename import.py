from sqlalchemy.engine import ResultProxy

from clean import DatabaseCleaner
from dedupe.deduplicator import Deduplicator
from gmaps_for_addresses import GoogleMapsScanner
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
from importer.npi_import import NPIImporter
from importer.nysdb_import import NYSDBImporter
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
        # LicenseCertMunger,
        # PhoneAddyMunger,
        # CredentialsMunger,
        # PaymentMunger,
        # AcceptedPlanMunger,
        # SpecialtyMunger,
        # LanguageMunger,
        # OrientationMunger,
        # GroupsMunger,
        # AcceptedPayorsMunger,
        # ModalityMunger,
        # AgeRangeMunger,
    )

    munger: Munger = Munger(plugins, plugin_debug)
    munger.update_fixtures()
    # Initial provider import
    munger.load_small_tables(tables)
    munger.process_providers(tables, update_provider_fields)
    cleaner = DatabaseCleaner()
    cleaner.clean()


def _truncate_db() -> None:
    print("** TRUNCATE PROVIDER!")
    session = NPIImporter.get_session()
    session.execute("TRUNCATE monday.provider CASCADE")
    session.execute("ALTER SEQUENCE monday.license_id_seq RESTART 1")
    session.close()


def full_import() -> None:
    base_path: str = '/Users/ixtli/Downloads/monday'
    loader: CSVLoader = CSVLoader(base_path)
    loader.load()
    tables = loader.get_tables()

    print("** FULL UPDATE!")
    _truncate_db()

    print("** Deduplicating")
    d = Deduplicator()
    d.build_zip_map()
    d.build_index(tables)
    d.update_map_destructively()
    del d

    plugin_debug = False
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
    del munger
    del tables

    print("\n\n**Import NPI Database")
    npi = NPIImporter()
    npi.load()
    npi.dedupe()
    npi.enrich()
    del npi

    print("\n\n**Import NYC Database")
    nyc = NYSDBImporter()
    nyc.load()
    nyc.match_rows_to_license_records()
    nyc.complex_match_rows()
    nyc.enrich()
    del nyc

    print("\n\n**Update Google Maps")
    gms = GoogleMapsScanner()
    gms.scan()
    gms.extract_zipcodes()
    gms.update()
    del gms

    print("\n\n**Clean")
    cleaner = DatabaseCleaner()
    cleaner.clean()


if __name__ == "__main__":
    # full_import()
    run_from_command_line()
