#!/usr/bin/env python
# coding=utf8

# Add tags folder to modules path
import sys
sys.path.append('./tags')
from datetime import datetime
import tag_creator

from google.cloud import datastore
import config

ds = datastore.Client(project=config.PROJECT_ID)

def retrievePouches(taglist):
  ''' Get the wordPouch for a tag from Datastore; if tag does not exist
        already, it is created

  Args:
    taglist (list): Indicates how to build Key for tags entity

  Returns:
    Array of wordPouch dicts for tags entities corresponding to single snippet
    Bin contains empty dict if tag could not be created
  '''

  snippetPouchArray=[]
  customPouchArray=[]
  for tagStr in taglist:
      # Iterating through each tag for the snippet
      tagSplit= tagStr.split('.')
      tag_key=''
      if len(tagSplit) == 1:
          #Tag contains only parent
          tag_key= datastore.Key("tags", tagSplit[0], project=config.PROJECT_ID)
      elif len(tagSplit) == 2:
          #Tag contains parent.child
          tag_key= datastore.Key("tags", tagSplit[0],"tags", tagSplit[1], project=config.PROJECT_ID)
      else:
          raise Exception('Incorrect argument for retrieval of tag entity')

      tag_dict= {}
      tag_ent = ds.get(key=tag_key)
      if tag_ent is None:
          #Create tag entity
          tag_ent= tag_creator.createCustomTag(tagStr)

      if tag_ent is not None:
          for i,word in enumerate(tag_ent['wordPouch']):
              tag_dict[word]= tag_ent['wordPouchScores'][i]

          if 'CUSTOM' in str(tag_ent.key):
              customPouchArray.append(tag_dict)
          else:
              snippetPouchArray.append(tag_dict)
  return (snippetPouchArray, customPouchArray)

def getArticleById(publisherId, articleId):
  ''' Get article by id from Datastore

  Args:
    publisherId (int): Publisher ID
    articleId (int): Article ID

  Returns:
    Article entity
  '''
  articleKey = datastore.Key('publishers', publisherId, 'articles', articleId, project=config.PROJECT_ID)
  article = ds.get(key=articleKey)
  return article

def getSnippetById(snippetId):
  ''' Get a snippet by id from Datastore

  Args:
    snippetId (int): Snippet ID

  Returns:
    Snippet entity
  '''
  snippetKey = datastore.Key('snippets', snippetId, project=config.PROJECT_ID)
  snippet = ds.get(key=snippetKey)
  return snippet

def getUnprocessedSnippets():
  ''' Get a snippet by id from Datastore

  Args:
    snippetId (int): Snippet ID

  Returns:
    Snippet entity
  '''
  query = ds.query(kind='snippets')
  #query.add_filter('wordPouch', '=', 'empty') #Datastore sucks, filter doesn't work
  snippets = list(query.fetch())
  snippets = [snip for snip in snippets if len(snip['wordPouch']) == 1]
  
  return snippets

def getSnippets():
  ''' Get all active snippets

  Args:
    None

  Returns:
    Snippets
  '''
  query = ds.query(kind='snippets')
  query.add_filter('status', '=', 'active') # Doesn't work - WTYF?!!?
  return list(query.fetch())

def saveEntity(entity):
  ds.put(entity)

def articlesBeforeDate():
  query = ds.query(kind='articles')
  query_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
  query.add_filter('createDate', '>=', query_date)

  articles = list(query.fetch())
  
  return articles

def articlesByPublisher(publisherId):
  ancestor = ds.key('publishers', publisherId)
  query = ds.query(kind='articles', ancestor=ancestor)
  return list(query.fetch())

def getPublisherArticlesByStatus(publisherId, status):
  query = ds.query(kind='articles')
  query.add_filter('status', '=', status)
  articles = list(query.fetch())
  publisherArticles = [article for article in articles if article.key.parent.id_or_name == publisherId]
  return publisherArticles

def updateStatus(entities, status):
  for ent in entities:
    ent['status'] = status
    saveEntity(ent)

def getArticlesWithSnippet(snippetId):
  query = ds.query(kind='articles')
  query.add_filter('snippetId', '=', snippetId)
  articles = list(query.fetch())
  #publisherArticles = [article for article in articles if article.key.parent.id_or_name == publisherId]
  return articles

def updateArticlesSnippetStatus(articles, status):
  for article in articles:
    currentStatus = article['snippetProperties']['status']
    print('DAL - updateArticlesSnippetStatus: updating staus [{}] => [{}] on snippet of article [{}]'.format(currentStatus, status, article.key.id_or_name))
    article['snippetProperties']['status'] = status
    saveEntity(article)

if __name__ == '__main__':
  #print(len(articlesBeforeDate()))
  #print(len(getSnippets()))
  
  '''articles = getPublisherArticlesByStatus('gadgety.co.il', 'assigned')
  print('TOTAL', len(articles))
  for a in articles:
    print(a.key.id_or_name, ' - ', a['snippetId'] if 'snippetId' in a else '?');'''
  
  #updateStatus(articles, 'inactive')

  '''articles = getArticlesWithSnippet(5725107787923456)
  print(len(articles))
  updateArticlesSnippetStatus(articles, 'inactive')'''

  articles = getArticlesWithSnippet(5769015641243648)
  articles = [article for article in articles if article.key.parent.id_or_name == 'gadgety.co.il']
  #print(len(articles))
  updateArticlesSnippetStatus(articles, 'inactive')
  #lenPerArticle = {article.key.id_or_name: len(article["content"].split(' ')) for article in articles}
  #lengths = [len(article["content"].split(' ')) for article in articles]
  #print(lenPerArticle)

  
  