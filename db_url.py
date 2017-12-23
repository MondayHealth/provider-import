import os

BASE_URL = "postgresql://postgres:changeme123@{}:5432/postgres"

HOSTS = {
    'eddingtonlimit.local': 'localhost',
    'pulsar.local': 'eddingtonlimit.local'
}

# Cache this
_node_name = os.uname()[1]


def get_db_url() -> str:
    """ Dynamically get a PostgreSQL db connection string based on the env """
    assert _node_name in HOSTS, "No DB host for node '{}'".format(_node_name)
    return BASE_URL.format(HOSTS[_node_name])
