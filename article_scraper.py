#!/usr/bin/env python
# coding=utf8

import logging
import requests
from google.cloud import datastore
from google.cloud import error_reporting
import google.cloud.logging

# Custom modules
import config
from common.helpers import scrape
from common import DAL

#Update article entity by adding scraped content
def updateArticleEnt(publisherId, articleId, content, title):
  #Retrieve article from Google Cloud Datastore
  article_key = datastore.Key("publishers", publisherId, "articles", str(articleId), project=str(config.PROJECT_ID))
  article_ent = DAL.getArticleById(publisherId, articleId)

  #Update article's content and status
  article_ent["title"]= title
  article_ent["content"]= content
  article_ent["status"] = "scraped"

  #Return updated article to datastore
  DAL.saveEntity(article_ent)

#Sends post request to snippet-matching function
def initiatePost(articleId, publisherId, lang):
    requests.post('https://simoti-171512.appspot.com/charlie', json = {"articleId": articleId,"publisherId": publisherId, "lang": lang})

def process(publisherId, articleId, articleUrl, language):
  '''Scrapes the article, updates the Article entity in datastore, and then initiates smart snippet-matching function

  Args:
    publisherId (int): Publisher ID
    articleId (int): Article ID
    articleUrl (str): Article URL
    language (str): Article language

  Returns:
    content (str): text from article
  '''
  (content, title) = scrape(articleUrl, language)
  updateArticleEnt(publisherId, articleId, content, title)
  initiatePost(articleId, publisherId, language)
  return content

# Execute if run independantly
if __name__ == '__main__':
  # print(process('gadgety.co.il', '183738', 'http://www.gadgety.co.il/183738/spiderman-homecoming-review/', 'he'))
  process('martech.zone', 'randy-stocklin-ecommerce', 'https://martech.zone/randy-stocklin-ecommerce/', 'en')
