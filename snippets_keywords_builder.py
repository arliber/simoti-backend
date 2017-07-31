#!/usr/bin/env python
# coding=utf8

# Add common fodler to modules path
import sys
sys.path.append('./common')

import requests as req
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import scipy
import operator
import regex as re
import json

# Custom modules
from helpers import getStopWords, scrape
from DAL import getSnippetById, saveEntity, getUnprocessedSnippets
import config


def getQueryUrls(query, language = 'en'):
  ''' Get a list of results URLs for the specified query, using Google Custome Engine

  Args:
    query (str): A query to search google for

  Returns:
    A list of all results links
  '''
  queryUrl = 'https://www.googleapis.com/customsearch/v1?key={}&cx={}&q={}'
  res = req.get(queryUrl.format(config.SEARCHENGINES[language]['key'], config.SEARCHENGINES[language]['id'], query))
  queryResults = res.json()
  if 'items' in queryResults:
    urls = [item['link'] for item in queryResults['items']]
  else:
    urls = []
    print('snippets_keywords_builder - getQueryUrls: no search results for [{}]'.format(query))

  return urls


def getTopNFeatures(vectorizer, matrix):
  ''' Get to N features from the sparse TF-IDF matrix

  Args:
    N (int): Amount of features to return
    vectorizer (TfidfVectorizer): TfidfVectorizer
    matrix (Sparse matrix): TF-IDF scores

  Returns:
    Top N features with their weights
  '''
  features = vectorizer.get_feature_names()
  topFeatures = {}

  for i in range(0, matrix.shape[0]):
      row = matrix.getrow(i).toarray()[0].ravel()
      topIndicies = row.argsort()
      for j in range(0, matrix.shape[1]):
          tempFeature = features[topIndicies[j]]
          topFeatures[tempFeature] = topFeatures.get(tempFeature, 0) + row[topIndicies[j]]

  topFeatures = sorted(topFeatures.items(), key = operator.itemgetter(1), reverse=True) # Sort
  return topFeatures

def getNGrams(word, corpus, language='en'):
  ''' Get bigrams and trigrams from articles based on supplied word

  Args:
    word (str): The word to base the N-Grams of of
    articles (list of strings): All articles texts

  Returns:
    A set of all bigrams and trigrams in articles
  '''

  preBigrams = re.findall(r'(\p{L}+\s+'+re.escape(word)+r')', corpus, re.M|re.I)
  sufBigrams = re.findall(r'('+re.escape(word)+r'\s+\p{L}+)', corpus, re.M|re.I)
  preTrigrams = re.findall(r'(\p{L}+\s+\p{L}+\s+'+re.escape(word)+r')', corpus, re.M|re.I)
  sufTrigram = re.findall(r'('+re.escape(word)+r'\s+\p{L}+\s+\p{L}+)', corpus, re.M|re.I)

  nGrams = preBigrams + sufBigrams + preTrigrams + sufTrigram
  nGrams = [ngram for ngram in nGrams if re.findall(r'(\w+)', ngram, re.M|re.I)[-1] not in getStopWords(language)]
  nGrams = [ngram for ngram in nGrams if re.findall(r'(\w+)', ngram, re.M|re.I)[0] not in getStopWords(language)]

  duplicateNGrams = set([x for x in nGrams if nGrams.count(x) > 1])
  uniqueNGrams = set(nGrams)

  return (duplicateNGrams, uniqueNGrams)

def getPhrases(features, articles, language='en'):
  ''' Get a dictionary of frequency and ngrams

  Args:
    features (list): All features
    articles (list): A list of all scraped articles

  Returns:
    A dictionary of weights and N-Grams
  '''

  # Build corpus based on scraped articles and clean it
  corpus = ','.join(articles).lower()
  corpus = re.sub(r'(\n)+', ' ', corpus)

  phrases = {}
  for i in range(0, len(features)):

      originalScore = features[i][1]
      loweredScore = originalScore * config.snippetsKeywordsBuilder['nGramsToDupNgramsRation']

      (duplicateNGrams, uniqueNGrams) = getNGrams(features[i][0], corpus, language)

      phrases[originalScore] = phrases.get(originalScore, set()) | duplicateNGrams
      phrases[loweredScore] = phrases.get(loweredScore, set()) | uniqueNGrams

  return phrases


def saveSnippetKeywords(snippet, weightedNGrams):
  ''' Save snippet N-Gram

  Args:
    snippet (entity): Snippet entity to udpate
    weightedNGrams (dictionary): Dicionary of weight and N-Grams
  '''

  ''' # Save as an embedded entity
  snippet['calculatedKeywords'] = datastore.Entity(key=ds.key('calculatedKeywords'))
  for weight in weightedNGrams:
      for nGram in weightedNGrams[weight]:
          snippet['calculatedKeywords'][nGram] = weight '''

  # Save as two seperate fields
  snippet['wordPouch'] = []
  snippet['wordPouchScores'] = []
  for weight in weightedNGrams:
    for nGram in weightedNGrams[weight]:
      snippet['wordPouch'] = snippet['wordPouch'] + [nGram]
      snippet['wordPouchScores'] = snippet['wordPouchScores'] + [weight]

  saveEntity(snippet)


def resultSummary(weightedNGrams, snippetId):
  ''' Returns a user-firlendly summary of of the process

  Args:
    weightedNGrams (dictionary): Dicionary of weight and N-Grams
    snippetId (int): Snippet ID

  Returns:
    String with summary
  '''
  ngramsCount = [len(weightedNGrams[k]) for k in list(weightedNGrams.keys())]
  return 'Saved {} N-Grams based on {} weights for snippet {}'.format(
      sum(ngramsCount),
      len(weightedNGrams),
      snippetId)

def inspectMatrix(TfIdfMatrix, vectorizer):
  features = vectorizer.get_feature_names()
  print('Built matrix with {} features: '.format(len(features)), features)

  row = TfIdfMatrix.toarray()[0]
  index = np.argmax(row)

  print('Matrix shape: ', TfIdfMatrix.shape)
  print('Most popular item is', features[index], 'with value', row[index] , 'at index', index)

def getUnprocessedSnippetIds():
  return [snip.key.id for snip in getUnprocessedSnippets()]
  
def setMultipleSnippetWeightedKeywords(snippetIds):
  summaries = { }
  print('snippets_keywords_builder - setMultipleSnippetWeightedKeywords: working on {} snippets'.format(len(snippetIds)))

  for snippetId in snippetIds:
    print('snippets_keywords_builder - setMultipleSnippetWeightedKeywords: working on snippet [{}]'.format(snippetId))
    summaries[snippetId] = setSnippetWeightedKeywords(snippetId)

  return summaries

def setSnippetWeightedKeywords(snippetId):
  ''' Find, weight and save related bigrams and trigrams for selected snipept

  Args:
    snippetId (int): Snippet ID

  Returns:
    String summary of the process
  '''
  snippet = getSnippetById(snippetId)
  print('Found snippet id [', snippetId, ']')

  searchQuery = snippet.get('searchQuery', snippet.get('title', ''))
  urls = getQueryUrls(searchQuery, snippet['language'])
  print('Found {} search results for [{}]'.format(len(urls), searchQuery))
  print(urls)

  articles = [scrape(url, snippet['language'])[0] for url in urls if not re.compile(r'\.pdf$', re.M|re.I).search(url)]
  print('Scraped {} articles'.format(len(articles)))

  if len(articles):
      # Build TF-IDF matrix
      stopWords = getStopWords(snippet['language'])
      vectorizer = TfidfVectorizer(max_df=0.6,
                                   min_df=0.2,
                                   ngram_range=(1, 3),
                                   lowercase=True,
                                   max_features=config.snippetsKeywordsBuilder['maxFeatures'],
                                   stop_words=stopWords)
      TfIdfMatrix = vectorizer.fit_transform(articles)

      inspectMatrix(TfIdfMatrix, vectorizer)

      topFeatures = getTopNFeatures(vectorizer, TfIdfMatrix)
      print('Top features are:', topFeatures)

      topFeaturesNormalized = [(feature[0],feature[1]/topFeatures[0][1]) for feature in topFeatures] #topFeatures[0][1] is the max value (ordered list)
      print('Top features normazlied:', topFeaturesNormalized)

      weightedNGrams = getPhrases(topFeaturesNormalized, articles, snippet['language'])
      # print('N grams:', weightedNGrams)

      saveSnippetKeywords(snippet, weightedNGrams)

      return resultSummary(weightedNGrams, snippetId)
  else:
      return 'no relevant articles found'

# Exectue if run independantly
if __name__ == '__main__':
  #print(setSnippetWeightedKeywords(5700305828184064)) #5682617542246400
  print(getUnprocessedSnippetIds())