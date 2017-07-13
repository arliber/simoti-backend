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

  publisherId = data.get('publisherId')
  articleId = data.get('articleId')
  articleUrl = data.get('articleUrl')
  language = data.get('language')

  if not data or not publisherId or not articleId or not articleUrl or not language:
      return make_response('Missing data', 400)

  article = article_scraper.process(publisherId, articleId, articleUrl, language)
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

  tag_creator.parseXML(str(topTag))
  res= "Created tags for tree below " + str(topTag)
  return json.dumps({'summary': res})


# This is only used when running locally. When running live, gunicorn runs
# the application.
if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8080, debug=True)

  