# Install
This package uses a virtual environment (venv) which you can read up on here:
https://docs.python.org/3/tutorial/venv.html

The tl;dr: is to run `./venv/bin/pip install -r requirements.txt`

# Development
Any time you add a dep (either in pycharm or cli) you should freeze the reqs
by doing something like `./venv/bin/pip freeze > requirements.txt`