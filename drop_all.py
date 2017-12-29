import configparser as configparser

from sqlalchemy import create_engine

from db_url import get_db_url
from provider.models.directories import Directory
from provider.models.providers import Provider

config = configparser.ConfigParser()
config.read("alembic.ini")
url = get_db_url()
engine = create_engine(url, echo=True)
Provider.metadata.drop_all(engine)
Directory.metadata.drop_all(engine)
Directory.metadata.create_all(engine)
Provider.metadata.create_all(engine)

# Reset all sequences
LIST_SEQUENCES = "SELECT c.relname FROM pg_class c WHERE c.relkind = 'S';"
SEQUENCES = []
for row in engine.execute(LIST_SEQUENCES):
    engine.execute("ALTER SEQUENCE monday.{} RESTART WITH 1;".format(row[0]))
