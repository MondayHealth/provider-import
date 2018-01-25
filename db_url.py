import os

from sqlalchemy.engine.url import URL

BASE_URL = "postgresql+psycopg2://{user}:{pass}@{host}:{port}/{db}"
DEFAULT = {'database': 'postgres', 'host': 'localhost', 'username': 'postgres',
           'password': 'changeme123', 'port': 5432,
           'drivername': 'postgresql+psycopg2', 'query': None}

RP = "bn{H2bD.^Q%d7ndgz97y"

HOSTS = {
    'pulsar': {'username': 'ixtli', 'password': ''},
    'eddingtonlimit': {'username': 'root', 'password': RP, 'port': 9999},
    'eddingtonlimit.local': {'username': 'root', 'password': RP, 'port': 9999}
}

# Cache this
_node_name = os.uname()[1]


def get_db_url() -> URL:
    """ Dynamically get a PostgreSQL db connection string based on the env """
    if _node_name in HOSTS:
        args = {**DEFAULT, **HOSTS[_node_name]}
    else:
        args = DEFAULT

    return URL(**args)
