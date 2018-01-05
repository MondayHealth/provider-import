import pycountry

LANGUAGE_CODE_MAP = {}

for lang in pycountry.languages:
    LANGUAGE_CODE_MAP[lang.alpha_3] = lang.name.lower()

# HARDCODE

# This can mean one of several dialects
LANGUAGE_CODE_MAP['jjj'] = 'fujianese'

# So can this, but it's likely taiwanese hokkien which doesnt have a code
LANGUAGE_CODE_MAP['ttt'] = 'taiwanese'

# We need this because there are 37 creoles in the dict but people use this
# phrase to describe some languages.
LANGUAGE_CODE_MAP['ccc'] = 'creole'