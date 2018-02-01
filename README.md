# Install
## System requirements
You must have python3.6 installed. Do this with homebrew. Install `Postgres10+`
and `postgis` using homebrew. Before doing anything, make sure you can connect
to postgres localy and that you do `CREATE EXTENSION postgis` followed by
`CREATE EXTENSION postgis_topology`.

Further, to use any functionality related to deduplication, you must be running
redis 4+ locally. To do this just `brew install redis`.

## virtualenv
It is highly recommended to use a virtual environment (venv) which you can read
up on here: https://docs.python.org/3/tutorial/venv.html.

Before doing anything you may want to `source venv/bin/activate`

### Usage
When you check this repo out for the first time you want to run
`python3 -m venv venv` which should create a new directory called 'venv' which
is excluded from source control. Then run
`./venv/bin/pip install -r requirements.txt` which will install requirements in
the venv. Then, when you're ready to dev, you can either continue running apps
out of the `./venv/bin/` directory OR you can run the `./venv/bin/activate`
script which will configure your current shell in such a way that it only uses
the current venv.

### Run
1. Set up the db with `alembic upgrade head` from the roo
1. Generate deduplication indicies by running `build_dedup_maps.py`
1. Import the XLS files by running `import.py`
1. Update address lat/lng points by running `gmaps_for_addresses.py`
1. Clean and update indicies by running `clean.py`

# Development
## Dependencies
Any time you add a dep (either in pycharm or cli) you should freeze the reqs
by doing something like `./venv/bin/pip freeze > requirements.txt`
