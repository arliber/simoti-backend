#!/usr/bin/env python
# coding=utf8

# Add common fodler to modules path
import sys
sys.path.append('./')
sys.path.append('../')

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction import stop_words
import numpy as np

# Custom modules
from common.helpers import getStopWords
from common.DAL import getArticleById, getSnippets

def getFrequencyMatrix(article, language='en'):
  stopWords = getStopWords(language)
  vectorizer = TfidfVectorizer(ngram_range=(1, 3),
                                  lowercase=True,
                                  max_features=None,
                                  stop_words = stopWords)
  TfIdfMatrix = vectorizer.fit_transform(article)
  return (TfIdfMatrix.toarray()[0], vectorizer.get_feature_names())


def getScoredDicionary(snippets):   
  snippetsDict = {}
  for i in range(0, len(snippets)):
      for j in range(0, len(snippets[i]['wordPouch'])):
          featureName = snippets[i]['wordPouch'][j]
          snippetsDict[featureName] = snippetsDict.get(featureName, [0] * len(snippets))
          snippetsDict[featureName][i] = snippets[i]['wordPouchScores'][j]
  return snippetsDict

def getScore(publisherId, articleId):

  # Handle article
  article = getArticleById(publisherId, articleId)
  (freq, feat) = getFrequencyMatrix([article['content']], 'en') # TODO: Save and get language from article! (not publihser)


  #### TESTS ####
  # TODO: Remove that!
  feat.append('MaaS ecosystem')
  freq = np.append(freq, 1)
  #### TESTS ####


  # Create feature: value dictionary
  articleDict = {feat[i]: freq[i] for i in range(0, min(len(feat), len(freq)))} 

  # Handle the snippets
  snippets = getSnippets()
  snippetsDict = getScoredDicionary(snippets)

  # Common words between all snippets
  commonWords = [dup for dup in snippetsDict if 0 not in snippetsDict[dup]]
  print('Common words between all {} snippets:'.format(len(snippets)), commonWords)

  # Multiply dictionaries
  scoredSnippets = {}
  for i in range(0, len(snippets)):
    snippetId = snippets[i].key.id
    for key in articleDict.keys():
      keyScore = articleDict[key] * snippetsDict.get(key, [0] * len(snippets))[i]
      if(keyScore > 0):
        scoredSnippets[snippetId] = scoredSnippets.get(snippetId, {})
        scoredSnippets[snippetId]['score'] = scoredSnippets[snippetId].get('score', 0) + keyScore
        scoredSnippets[snippetId]['commonWords'] = scoredSnippets[snippetId].get('commonWords', set()) | {key}

  return scoredSnippets

if __name__ == '__main__':
  print(getScore('martech.zone', 'ecommerce-shipping-options'))
