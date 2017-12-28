import configparser as configparser

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from db_url import get_db_url
from provider.models.providers import Provider
from provider.models.directories import Directory

config = configparser.ConfigParser()
config.read("alembic.ini")
url = get_db_url()
engine = create_engine(url, echo=True)
Provider.metadata.drop_all(engine)
Directory.metadata.drop_all(engine)
Directory.metadata.create_all(engine)
Provider.metadata.create_all(engine)
