#!/usr/bin/env python

import config
import logging
import requests
from google.cloud import datastore
from google.cloud import error_reporting
import google.cloud.logging
from newspaper import Article

def scrape(url, language='en'):
  ''' Scrape given url using supplied or default language

  Args:
    url (str): Article's URL for parsing
    language (str, optional): Language to parse in. Defaults to 'en'

  Returns:
    Parsed text if succeeds, empty string otherwise
  '''
  page = Article(url = url, language = language)
  attempts = 0
  success = False
  # Exception raised following this bug: https://github.com/codelucas/newspaper/issues/357
  while(attempts < 4):
      try:
          attempts += 1
          page.download()
          page.parse()
          success = True
          break
      except BaseException as e:
          print('Error in parsing {}, attempt #{}'.format(url, attempts) , str(e))
          pass

  return page.text if success else ''

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
