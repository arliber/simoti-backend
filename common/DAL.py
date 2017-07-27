#!/usr/bin/env python
# coding=utf8

# Add tags folder to modules path
import sys
sys.path.append('./tags')
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
  # query.add_filter('status', '=', 'active') # Doesn't work - WTYF?!!?
  return list(query.fetch())

def saveEntity(entity):
  ds.put(entity)

def getEmbeddedEntityObject():
  return datastore.Entity(key=ds.key('EmbeddedKind'))
