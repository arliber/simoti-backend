#!/usr/bin/env python

#__author__ = "Logan Horowitz, Arik Liber"
#__copyright__ = "Copyright 2017, Simoti Co"
#__version__ = "1.0.1"
#__status__ = "Production"


#-----------------Imports-----------------

#For debugging
import logging

#For flask app creation and http request/response
from flask import current_app, Flask, redirect, url_for, request
import requests
import json

#For datastore access
#import datastore
from google.cloud import datastore as datastore
#import google.cloud.datastore.key
#import error_reporting
from google.cloud import error_reporting

import google.cloud.logging

#For scraping
import newspaper
from newspaper import Article

import snippets_keywords_builder
#-----------------------------------------


#-----------------Methods-----------------

#scrapes website and returns article content
def scrape(urlstr, lang):
    art= Article(url=urlstr, language= lang)
    art.download()
    art.parse()
    return art.text


#Update article entity by adding scraped content
def updateArticleEnt(pID,keyPub, keyNum, content):
    #Retrieve article from Google Cloud Datastore
    ds = datastore.Client(project= str(pID))
    article_key= datastore.Key("publishers", keyPub,"articles", str(keyNum), project=str(pID))
    article_ent = ds.get(key=article_key)

    #Update article's content and status
    article_ent["content"]= content
    article_ent["status"]= "scraped"

    #Return updated article to datastore
    ds.put(article_ent)


#Sends post request to snippet-matching function
def initiatePost(content, keyPub, keyNum, lang):
    #TODO: Add a smart_function_url
    requests.post('smart_function_url', data = {"content": content,"publisher": keyPub, "articleNumber": keyNum, "lang": lang})


#Scrapes the article, updates the Article entity in datastore, and then
#initiates smart snippet-matching function
def process(pID,keyPub,keyNum, url, lang):
    content= scrape(url, lang)
    updateArticleEnt(pID,keyPub,keyNum, content)
    initiatePost(content, keyPub, keyNum, lang)
#-----------------------------------------


#---------------App Creation--------------

def create_app(config):
    #TODO: adjust Flask input arg to reflect package or move all to one file
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
            return make_response("Missing Data", 500)

        process(config.PROJECT_ID,keyPub, keyNum, url, lang)
        return json.dumps({})

    @app.route('/buildSnippetKeywords', methods=['POST'])
    def buildSnippetKeywords():
        data = request.get_json()

        snippetId = data.get('snippetId')

        if not data or not snippetId:
            return make_response('No snippet id supplied', 404)

        res = snippets_keywords_builder.setSnippetWeightedKeywords(snippetId)
        return json.dumps({'result': res})

    return app
#-----------------------------------------