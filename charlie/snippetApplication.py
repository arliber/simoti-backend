#!/usr/bin/env python
# coding=utf8

from common.DAL import getSnippetById, getArticleById, saveEntity, getEmbeddedEntityObject

def getHostingParagraphs(article, commonWords):
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
  bestPairIndex = pairsScore.index(max(pairsScore))    

  return (paragraphs[bestPairIndex], paragraphs[bestPairIndex+1])


def applySnippet(articleId, publisherId, snippetId, commonWords):
  snippet = getSnippetById(snippetId)
  article = getArticleById(publisherId, articleId)
  (paragraphBefore, paragraphAfter) = getHostingParagraphs(article['content'], commonWords)
  #article['snippetProperties'] = getEmbeddedEntityObject()
  article['status'] = 'assigned'
  article['snippetProperties']['status'] = 'active'
  article['snippetProperties']['position'] = 'beforeAfterContent'
  article['snippetProperties']['contentAfter'] = paragraphAfter[:20]
  article['snippetProperties']['contentBefore'] = paragraphBefore[:20]
  
  print('snippetApplication - applySnippet: Saving snippet [{}]'.format(snippetId), article['snippetProperties'])
  saveEntity(article)
