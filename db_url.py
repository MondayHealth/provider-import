import os

_BASE_URL = "postgresql://postgres:changeme123@{}:5432/postgres"
_HOSTS = {
    'eddingtonlimit.local': 'localhost',
    'pulsar.local': 'eddingtonlimit.local'
}
DB_URL = _BASE_URL.format(_HOSTS[os.uname()[1]])
