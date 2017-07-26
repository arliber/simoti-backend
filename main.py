#!/usr/bin/env python

from flask import current_app, Flask, redirect, url_for, request, Response
import requests
import json

import config
import article_scraper
import snippets_keywords_builder
from tags import tag_creator
from charlie import Charlie
from charlie import snippetApplication
from time import sleep, time

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
  print('/scrapeArticle - starting with data ', data)

  publisherId = data.get('publisherId')
  articleId = data.get('articleId')
  articleUrl = data.get('articleUrl')
  language = data.get('language')

  if not data or not publisherId or not articleId or not articleUrl or not language:
      print('/scrapeArticle - missing some data, got ', data)
      return Response(response= 'Missing data', status= 400)

  article = article_scraper.process(publisherId, articleId, articleUrl, language)
  print('/scrapeArticle - scraped article [{}] from [{}] of length {} for publisher {}'.format(articleId, articleUrl, len(article), publisherId))

  return json.dumps({'article': article})

@app.route('/buildSnippetKeywords', methods=['POST'])
def buildSnippetKeywords():
  data = request.get_json()
  snippetId = data.get('snippetId')
  if not data or not snippetId:
      return Response(response= 'No snippet id supplied', status=404)

  res = snippets_keywords_builder.setSnippetWeightedKeywords(snippetId)
  return json.dumps({'summary': res})

@app.route('/createTags', methods=['POST'])
def createTags():
  data = request.get_json()
  topTag = data.get('topTag')
  if not data or not topTag:
      return Response(response= 'No starting tag supplied', status=500)

  badTags= tag_creator.parseXML(str(topTag))
  badStr= ''
  for tag in badTags:
      badStr+= str(tag) + ' '
  return json.dumps({'badTags': badStr})

@app.route('/charlie', methods=['POST'])
def charlie():
  data= request.get_json()
  articleId= data.get('articleId')
  publisherId= data.get('publisherId')
  language= data.get('lang')

  if not data or not articleId or not publisherId or not language:
      return Response(response='Incorrect data supplied to charlie', status=500)

  # Start logic
  selectedSnippet = Charlie.makeSnippetSelection(articleId, publisherId, language)
  print('selectedSnippet', selectedSnippet)
  if selectedSnippet is not None:
    snippetApplication.applySnippet(articleId, publisherId, selectedSnippet['snippetId'], selectedSnippet['commonWords'])
    postResult = requests.post('https://snips.simoti.co/applySnippet', json = {"snippetId": selectedSnippet['snippetId'], "publisherId": publisherId, "articleId": articleId})
    return json.dumps({'snippetId': selectedSnippet['snippetId']})
  else:
    return json.dumps({})

@app.route('/adServerPing', methods=['GET'])
def adServerPing():
  print('/adServerPing: PING AD SERVER')
  startTime = time()
  i = 0
  while time() < startTime + 50:
    i += 1
    requests.get('https://snips.simoti.co/getSnippet')

  print('/adServerPing: performed {} pings'.format(i))
  return json.dumps({'i': i, 'time': time() - startTime})

# This is only used when running locally. When running live, gunicorn runs
# the application.
if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8080, debug=True)
