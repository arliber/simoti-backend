#!/usr/bin/env python

from flask import current_app, Flask, redirect, url_for, request
import requests
import json

import config
import article_scraper
import snippets_keywords_builder
import tag_creator


app = Flask(__name__)
app.config.from_object(config)

# Configure logging
#ADD THIS BACK FOR DEPLOYMENT#client = google.cloud.logging.Client(app.config['PROJECT_ID'])
# Attaches a Google Stackdriver logging handler to the root logger
#ADD THIS BACK FOR DEPLOYMENT#client.setup_logging(logging.INFO)

# Receive POST from ad server and begin scrape/snippet matching process
@app.route('/scrapeArticle', methods=['POST'])
def scrapeArticle():
  data = request.get_json()

  keyPub = data.get('publisher')
  keyNum = data.get('articleNumber')
  url = data.get('url')
  lang = data.get('language')

  if not data or not keyPub or not keyNum or not url or not lang:
      return make_response('Missing data for scraper', 500)

  article = article_scraper.process(keyPub, keyNum, url, lang)
  return json.dumps({'article': article})

@app.route('/buildSnippetKeywords', methods=['POST'])
def buildSnippetKeywords():
  data = request.get_json()
  snippetId = data.get('snippetId')
  if not data or not snippetId:
      return make_response('No snippet id supplied', 404)

  res = snippets_keywords_builder.setSnippetWeightedKeywords(snippetId)
  return json.dumps({'summary': res})

@app.route('/createTags', methods=['POST'])
def createTags():
  data = request.get_json()
  topTag = data.get('topTag')
  if not data or not topTag:
      return make_response('No starting tag supplied', 500)

  badTags= tag_creator.parseXML(str(topTag))
  badStr= ''
  for tag in badTags:
      badStr+= str(tag) + ' '
  return json.dumps({'badTags': badStr})


# This is only used when running locally. When running live, gunicorn runs
# the application.
if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8080, debug=True)


  