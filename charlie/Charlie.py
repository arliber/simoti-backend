#!/usr/bin/env python
# coding=utf8

# Add tags folder to modules path
import sys
sys.path.append('./')
sys.path.append('../')

from charlie import snippetsScore, tagsScore

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction import stop_words
import numpy as np

import config
from common.DAL import getSnippets, getArticleById
from common.helpers import getStopWords


def getFrequencyMatrix(article, language):
  print('Charlie - getFrequencyMatrix: language [{}], article'.format(language), article)
  stopWords = getStopWords(language)
  vectorizer = TfidfVectorizer(ngram_range=(1, 3),
                                  lowercase=True,
                                  max_features=None,
                                  stop_words = stopWords)
  TfIdfMatrix = vectorizer.fit_transform(article)

  return (TfIdfMatrix.toarray()[0], vectorizer.get_feature_names())


# Computes overall score for each snippet, returns top n
def findTopSnippet(totalDict):

    topSnippet = {}
    for snippetId in totalDict.keys():
        tagsText = totalDict[snippetId].get('tagsTextScore',0) * config.CHARLIE['tagsTextWeight']
        tagsTitle = totalDict[snippetId].get('tagsTitleScore',0) * config.CHARLIE['tagsTitleWeight']
        customText = totalDict[snippetId].get('customTextScore',0) * config.CHARLIE['customTextWeight']
        customTitle = totalDict[snippetId].get('customTitleScore',0) * config.CHARLIE['customTitleWeight']
        snippetsText = totalDict[snippetId].get('snippetTextScore',0) * config.CHARLIE['snippetsTextWeight']
        snippetsTitle = totalDict[snippetId].get('snippetTitleScore',0) * config.CHARLIE['snippetsTitleWeight']
        score = tagsText+tagsTitle+customText+customTitle+snippetsText+snippetsTitle

        print('Charlie - findTopSnippet: SnippetId: {} , Total Score: {} , Individual Scores: ( {} {} {} {} {} {} )'.format(snippetId,score,tagsText,tagsTitle,customText,customTitle,snippetsText,snippetsTitle))

        if score > topSnippet.get('score', 0):
            topSnippet['snippetId'] = snippetId
            topSnippet['score'] = score
            topSnippet['commonWords'] = totalDict[snippetId]['commonWords']

    print('Charlie - findTopSnippet: selected snippet ', topSnippet)
    return topSnippet


# Aggregates various scores of snippets, computes overall score,
# and then selects snippet if score is high enough
def makeSnippetSelection(articleId, publisherId, language):

    # Handle article
    article = getArticleById(publisherId, articleId)
    
    if article['status'] == 'assigned':
        print('Charlie - makeSnippetSelection: article [{}][{}]is already assigned'.format(publisherId, articleId))
        return None
    else:
        print('Charlie - makeSnippetSelection: working on article [{}][{}]'.format(publisherId, articleId))
        if article['content'] == '':
            print('Charlie - makeSnippetSelection: content is empty')
            return None

        (contentFreq, contentFeat) = getFrequencyMatrix([article['content']], language)
        title = article.get('searchQuery', article.get('title', ''))
        (titleFreq, titleFeat) = getFrequencyMatrix([article['title']], language)
        # Create feature: value dictionaries
        articleContentDict = {contentFeat[i]: contentFreq[i] for i in range(0, min(len(contentFeat), len(contentFreq)))}
        articleTitleDict = {titleFeat[i]: titleFreq[i] for i in range(0, min(len(titleFeat), len(titleFreq)))}

        #Handle snippets using snippetsScore.py and tagsScore.py
        snippetEntities = getSnippets()
        snippetDict = snippetsScore.getScore(snippetEntities, articleContentDict, articleTitleDict)
        tagsDict = tagsScore.getTagScores(snippetEntities, articleContentDict, articleTitleDict)

        #Compile the scores into one dict
        totalDict = {}
        idList = set(tagsDict.keys()) | set(snippetDict.keys())
        for snippetId in idList:
            allScoresDict = {}
            if snippetId in tagsDict:
                allScoresDict['tagsTextScore']= tagsDict[snippetId]['textScore']
                allScoresDict['tagsTitleScore']= tagsDict[snippetId]['titleScore']
                allScoresDict['customTextScore']= tagsDict[snippetId]['customTextScore']
                allScoresDict['customTitleScore']= tagsDict[snippetId]['customTitleScore']
                allScoresDict['commonWords'] = allScoresDict.get('commonWords', set()) | set(tagsDict[snippetId]['commonWords'])

            if snippetId in snippetDict:
                allScoresDict['snippetTextScore'] = snippetDict[snippetId].get('contentScore', 0)
                allScoresDict['snippetTitleScore'] = snippetDict[snippetId].get('titleScore', 0)
                allScoresDict['commonWords'] = allScoresDict.get('commonWords', set()) | set(snippetDict[snippetId]['commonWords'])

            totalDict[snippetId]= allScoresDict

        #Return snippet with highest overall score
        topSnippet = findTopSnippet(totalDict)

        return topSnippet if topSnippet.get('score', 0) > config.CHARLIE['scoreThreshold'] else None 


if __name__ == '__main__':  
  #print(makeSnippetSelection('business-case-for-dam', 'martech.zone', 'en'))
  print(makeSnippetSelection('185489', 'gadgety.co.il', 'he'))
