#!/usr/bin/env python
# coding=utf8

import sys
sys.path.append('./')
sys.path.append('../')
from common.DAL import getSnippetById, getArticleById, saveEntity
import article_scraper

def getHostingParagraphs(article, commonWords):
  print('snippetApplication - getHostingParagraphs: common words are ', commonWords)
  paragraphs = [paragraph.strip() for paragraph in article.splitlines() if paragraph != '']

  words = [paragraph.strip() for paragraph in article.split() if paragraph != '']
  wordsCount = len(words)

  paragraphLengthWeights = [0]
  for i in range(0, len(paragraphs)):
    paragraphWords = len(paragraphs[i])
    paragraphLengthWeights = paragraphLengthWeights + [paragraphLengthWeights[i] + paragraphWords/wordsCount]

  paragraphLengthWeights = paragraphLengthWeights[1:] # Remove leading 0     
    
  keywordsCount = []
  for paragraph in paragraphs:
    keywordsCount = keywordsCount + [sum(k in paragraph for k in commonWords)]
    
  paragraphWeights = []
  for i in range(0, len(paragraphs)):
    paragraphWeights = paragraphWeights + [-1*paragraphLengthWeights[i] + keywordsCount[i]]

  pairsScore = [paragraphWeights[i]+paragraphWeights[i+1] for i in range(0,len(paragraphWeights[:-1]))]
  
  if len(pairsScore) > 0:
    bestPairIndex = pairsScore.index(max(pairsScore))    
    return (paragraphs[bestPairIndex], paragraphs[bestPairIndex+1])
  else:
    return (None, None)


def applySnippet(articleId, publisherId, snippetId, commonWords):
  snippet = getSnippetById(snippetId)
  article = getArticleById(publisherId, articleId)

  if 'content' not in article or article['content'] == '': # Try scraping the article again if empty
    article_scraper.process(publisherId, articleId, article['url'], article.get('language', 'auto'))
    article = getArticleById(publisherId, articleId)
  
  (paragraphBefore, paragraphAfter) = getHostingParagraphs(article['content'], commonWords)
  
  if paragraphBefore is not None and paragraphAfter is not None:
    article['status'] = 'assigned'
    article['snippetProperties']['status'] = 'active'
    article['snippetProperties']['position'] = 'beforeAfterContent'
    article['snippetProperties']['contentAfter'] = paragraphAfter[:20]
    article['snippetProperties']['contentBefore'] = paragraphBefore[:20]
    
    print('snippetApplication - applySnippet: Saving snippet [{}]'.format(snippetId), article['snippetProperties'])
    saveEntity(article)
    return True
  else:
    print('snippetApplication - applySnippet: not applying snippet [{}] to {}/{} - no matching location was found'.format(snippetId, publisherId, articleId))
    return False

if __name__ == '__main__':
  applySnippet('185705', 'gadgety.co.il', 5725107787923456, [])