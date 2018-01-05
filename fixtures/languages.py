import pycountry

LANGUAGE_CODE_MAP = {}

for lang in pycountry.languages:
    LANGUAGE_CODE_MAP[lang.alpha_3] = lang.name.lower()

# HARDCODE

# This can mean one of several dialects
LANGUAGE_CODE_MAP['jj*'] = 'fujianese'

# So can this, but it's likely taiwanese hokkien which doesnt have a code
LANGUAGE_CODE_MAP['tt*'] = 'taiwanese'

# We need this because there are 37 creoles in the dict but people use this
# phrase to describe some languages.
LANGUAGE_CODE_MAP['cc*'] = 'creole'

# We should keep track of ESL specialties
LANGUAGE_CODE_MAP['es*'] = 'english as a second language'
