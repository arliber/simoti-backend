#!/usr/bin/env python
# coding=utf8

# Add common fodler to modules path
import sys
sys.path.append('./common')

import logging
import requests
from google.cloud import datastore
from google.cloud import error_reporting
import google.cloud.logging

# Custom modules
import config
from helpers import scrape


#Update article entity by adding scraped content
def updateArticleEnt(publisherId, articleId, content):
  #Retrieve article from Google Cloud Datastore
  ds = datastore.Client(project= str(config.PROJECT_ID))
  article_key = datastore.Key("publishers", publisherId, "articles", str(articleId), project=str(config.PROJECT_ID))
  article_ent = ds.get(key=article_key)

  #Update article's content and status
  article_ent["content"]= content
  article_ent["status"] = "scraped"

  #Return updated article to datastore
  ds.put(article_ent)

#Sends post request to snippet-matching function
def initiatePost(content, keyPub, keyNum, lang):
  #TODO: Add a smart_function_url
  requests.post('smart_function_url', data = {"content": content,"publisher": keyPub, "articleNumber": keyNum, "lang": lang})



def process(publisherId, articleId, articleUrl, language):
  '''Scrapes the article, updates the Article entity in datastore, and then initiates smart snippet-matching function

  Args:
    TBD
  
  Returns:
    TBD
  '''
  content = scrape(articleUrl, language)
  updateArticleEnt(publisherId, articleId, content)
  #initiatePost(content, keyPub, keyNum, lang)
  return content

# Exectue if run independantly
if __name__ == '__main__':
  # print(process('gadgety.co.il', '183738', 'http://www.gadgety.co.il/183738/spiderman-homecoming-review/', 'he'))
  print(process('martech.zone', 'randy-stocklin-ecommerce', 'https://martech.zone/randy-stocklin-ecommerce/', 'en'))
