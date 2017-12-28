import os

BASE_URL = "postgresql://{user}:{pass}@{host}:5432/{db}"
DEFAULT = {'db': 'postgres', 'host': 'localhost', 'user': 'postgres',
           'pass': 'changeme123'}

HOSTS = {
    'pulsar': {'user': 'ixtli', 'pass': ''}
}

# Cache this
_node_name = os.uname()[1]


def get_db_url() -> str:
    """ Dynamically get a PostgreSQL db connection string based on the env """
    if _node_name in HOSTS:
        return BASE_URL.format(**{**DEFAULT, **HOSTS[_node_name]})
    else:
        return BASE_URL.format(**DEFAULT)
