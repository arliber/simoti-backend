#!/usr/bin/env python

# The secret key is used by Flask to encrypt session cookies.
SECRET_KEY = 'secrets'

DATA_BACKEND = 'datastore'

# Google Cloud Project ID. This can be found on the 'Overview' page at
# https://console.developers.google.com
PROJECT_ID = 'simoti-171512'

# Google Custom Search engine credentials
SEARCHENGINES = { 'he': {}, 'en': {} }
SEARCHENGINES['he']['key'] = 'AIzaSyAx_o3OOlY92fsPUfQaUBzUlXG8-a-Zsm0'
SEARCHENGINES['he']['id'] = '000161978559585141097:55s91q7tm4q'
SEARCHENGINES['en']['key'] = 'AIzaSyAx_o3OOlY92fsPUfQaUBzUlXG8-a-Zsm0'
SEARCHENGINES['en']['id'] = '000161978559585141097:ueqmvvi3cc0'

# Snippets keywords builder
snippetsKeywordsBuilder = { }
snippetsKeywordsBuilder['maxFeatures'] = 12
snippetsKeywordsBuilder['nGramsToDupNgramsRation'] = 0.7

# Twitter API Access Values
consumer_key = '5We5CMiZamhDR0AzAeVlSq8jk'
consumer_secret = 'mnYfyCqJC0hEqw9Xw2DZJPz9r97DYBWbA3hK98EY69c2YfGcsV'
access_token = '12833912-fpmakSwu52RPjPry7VV5pzOCIlRq0RegjQ4zvkkom'
access_token_secret = 'EY5G6dmEXvGKoubm02MOYnZRPtnpSP5lf7M1q8xXTPEAf'

# Charlie
CHARLIE = { }
CHARLIE['scoreThreshold'] = 0.001
CHARLIE['tagsTextWeight'] = 5          #Related words to tags and article text
CHARLIE['tagsTitleWeight'] = 250       #Related words to tags and article title
CHARLIE['customTextWeight'] = 2.85714  #Related words to custom tags and article text
CHARLIE['customTitleWeight'] = 107.14  #Related words to custom tags and article title
CHARLIE['snippetsTextWeight'] = 0.75   #Related words to snippet title and article text
CHARLIE['snippetsTitleWeight'] = 31.25 #Related words to snippet title and article title
 