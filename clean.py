import configparser
from typing import Tuple, List

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session

from db_url import get_db_url


class DatabaseCleaner:
    TSVS: List[Tuple[str]] = [
        ("provider", "name_tsv", """
        coalesce(first_name,'') || ' ' || coalesce(middle_name,'') || ' ' 
            || coalesce(last_name,'')
        """),
        ("orientation",),
        ("group",),
        ("acceptedpayorcomment",),
        ("address", "formatted_tsv", "formatted")
    ]

    ECHO_SQL: bool = False

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("alembic.ini")
        url = get_db_url()
        print("Creating engine at", url)
        self._engine = create_engine(url, echo=self.ECHO_SQL)
        session_factory = sessionmaker(bind=self._engine)
        self._Session = scoped_session(session_factory)
        self._Session.configure()
        self._session: Session = self._Session()

    def _update_tsv(self, table: str, field: str = "tsv",
                    content: str = "body") -> None:
        print(table, field, content)
        self._session.execute(
            "UPDATE monday.{} SET {} = to_tsvector('english', {});".format(
                table, field, content))
        self._session.commit()

    def _update_tsvs(self) -> None:
        print("Updating TSVs ...")
        for t in self.TSVS:
            self._update_tsv(*t)
        print("Done.")

    def _update_geometries(self) -> None:
        print("CLUSTER geometries...")
        self._session.execute("""
        CLUSTER ix_monday_address_point_gist ON monday.address;
        """)
        self._session.commit()
        print("Done.")

    def _vacuum(self) -> None:
        # Do this so we dont hang.
        self._session.close()
        print("Calling VACUUM FULL VERBOSE ANALYSE ...")
        connection = self._engine.raw_connection()
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        cursor.execute("VACUUM FULL VERBOSE ANALYSE;")
        print("Closing connection...")
        connection.close()
        print("Done.")

    def clean(self):
        self._update_tsvs()
        self._update_geometries()
        self._vacuum()


if __name__ == "__main__":
    DatabaseCleaner().clean()
