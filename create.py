import configparser

from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
from sqlalchemy.sql.ddl import CreateSchema

from provider.models.base import Base


class Util:
    """
    Container class so we can avoid global vars
    """

    def __init__(self):
        config = configparser.ConfigParser()
        config.read("alembic.ini")
        url = config['alembic']['sqlalchemy.url']
        print("Creating engine at", url)
        self.engine = create_engine(url, echo=True)
        self.insp = reflection.Inspector.from_engine(self.engine)
        print("Binding engine to base table metadata")
        Base.metadata.bind = self.engine
        self.schema_name = Base.metadata.schema

    def _schema_exists(self) -> bool:
        return self.schema_name in self.insp.get_schema_names()

    def create(self) -> None:
        """
        To be run once to put the DB in a state where migrations can be run
        """
        if not self._schema_exists():
            self.engine.execute(CreateSchema(self.schema_name))
        else:
            print("Schema appears to exist. Skipping")

    def destroy(self) -> None:
        """
        To be run to destroy what create() did
        """
        if self._schema_exists():
            print("Dropping all records, tables, and types!")
            Base.metadata.drop_all()
            # self.engine.execute(DropSchema(self.schema_name))


if __name__ == "__main__":
    Util().destroy()
