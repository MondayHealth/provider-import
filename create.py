import configparser

from sqlalchemy import create_engine

from provider.models.base import Base

config = configparser.ConfigParser()
config.read("alembic.ini")
url = config['alembic']['sqlalchemy.url']
engine = create_engine(url, echo=True)

Base.metadata.create_all(engine)
