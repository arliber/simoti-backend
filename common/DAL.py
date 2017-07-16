#!/usr/bin/env python
# coding=utf8

from google.cloud import datastore
import config

ds = datastore.Client(project=config.PROJECT_ID)

def getArticleById(publisherId, articleId):
  ''' Get article bu id from Datastore

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

def getSnippets():
  ''' Get all active snippets

  Args:
    None

  Returns:
    Snippets
  '''
  query = ds.query(kind='snippets')
  # query.add_filter('status', '=', 'active') # Doesn't work - WTYF?!!?
  return list(query.fetch())

def saveEntity(entity):
  ds.put(entity)