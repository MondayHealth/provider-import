# Install
## System requirements
You must have python3.6 installed. Do this with homebrew.

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

# Development
## Dependencies
Any time you add a dep (either in pycharm or cli) you should freeze the reqs
by doing something like `./venv/bin/pip freeze > requirements.txt`
