#!/usr/bin/env python
# coding=utf8

# Add common fodler to modules path
import sys
sys.path.append('./')
sys.path.append('../')

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


def getScore(publisherId, articleId, language):

  # Handle article
  article = getArticleById(publisherId, articleId)
  (contentFreq, contentFeat) = getFrequencyMatrix([article['content']], language) # Article body
  (titleFreq, titleFeat) = getFrequencyMatrix([article['title']], language) # Article title
  print('titleFeat', titleFeat)

  # Create feature: value dictionaries
  articleContentDict = {contentFeat[i]: contentFreq[i] for i in range(0, min(len(contentFeat), len(contentFreq)))}
  articleTitleDict = {titleFeat[i]: titleFreq[i] for i in range(0, min(len(titleFeat), len(titleFreq)))}

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

    # Score content
    for key in articleContentDict.keys():
      keyScore = articleContentDict[key] * snippetsDict.get(key, [0] * len(snippets))[i]
      if(keyScore > 0):
        scoredSnippets[snippetId] = scoredSnippets.get(snippetId, {})
        scoredSnippets[snippetId]['contentScore'] = scoredSnippets[snippetId].get('contentScore', 0) + keyScore
        scoredSnippets[snippetId]['commonWords'] = scoredSnippets[snippetId].get('commonWords', set()) | {key}

    # Scroe title
    for key in articleTitleDict.keys():
      keyScore = articleTitleDict[key] * snippetsDict.get(key, [0] * len(snippets))[i]
      if(keyScore > 0):
        scoredSnippets[snippetId] = scoredSnippets.get(snippetId, {})
        scoredSnippets[snippetId]['titleScore'] = scoredSnippets[snippetId].get('titleScore', 0) + keyScore
        scoredSnippets[snippetId]['commonWords'] = scoredSnippets[snippetId].get('commonWords', set()) | {key}

  return scoredSnippets

if __name__ == '__main__':
  print(getScore('martech.zone', 'randy-stocklin-ecommerce', 'en'))
