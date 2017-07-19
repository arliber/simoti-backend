#!/usr/bin/env python
# coding=utf8

# Add tags folder to modules path
import sys
sys.path.append('./')
sys.path.append('../')

from charlie import snippetsScore

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction import stop_words
import numpy as np

from charlie import tagsScore
from common.DAL import getSnippets, getArticleById
from common.helpers import getStopWords

'''
  Run snippet scrore
  Run tags based score
  Apply predefined weights
  If score above predefined treshold - call compiler with article and selected snippet id

  IMPORTANT: Log, a lot
'''

scoreThreshold= 1

def getFrequencyMatrix(article, language):
  stopWords = getStopWords(language)
  vectorizer = TfidfVectorizer(ngram_range=(1, 3),
                                  lowercase=True,
                                  max_features=None,
                                  stop_words = stopWords)
  TfIdfMatrix = vectorizer.fit_transform(article)

  return (TfIdfMatrix.toarray()[0], vectorizer.get_feature_names())


# Computes overall score for each snippet, returns top n
def findTopSnippet(totalDict):

    # Weighting values we can play with
    tagsTextWeight= .5          #Related words to tags and article text
    tagsTitleWeight= 25         #Related words to tags and article title
    customTextWeight= .285714   #Related words to custom tags and article text
    customTitleWeight= 10.714   #Related words to custom tags and article title
    snippetsTextWeight= .075    #Related words to snippet title and article text
    snippetsTitleWeight= 3.125  #Related words to snippet title and article title

    finalDict= {}
    topScore= 0
    topID= ''
    for snippetId in totalDict.keys():
        tagsText= snippetId['tagsTextScore'] * tagsTextWeight
        tagsTitle= snippetId['tagsTitleScore'] * tagsTitleWeight
        customText= snippetId['customTextScore'] * customTextWeight
        customTitle= snippetId['customTitleScore'] * customTitleWeight
        snippetsText= snippetId['snippetTextScore'] * snippetsTextWeight
        snippetsTitle= snippetId['snippetTitleScore'] * snippetsTitleWeight
        score= tagsText+tagsTitle+customText+customTitle+snippetsText+snippetsTitle

        if score > topScore:
            topScore= score
            topID= snippetId

        finalDict['snippetId']= "Total: {} , Individual: {} {} {} {} {} {}...".format(score,tagsText,tagsTitle,customText,customTitle,snippetsText,snippetsTitle)
    print(finalDict)

    topSnippet={}
    topSnippet['snippetId']= topID
    topSnippet['score']= topScore
    return topSnippet


# Aggregates various scores of snippets, computes overall score,
# and then selects snippet if score is high enough
def makeSnippetSelection(articleId, publisherId, language):

    global scoreThreshold

    # Handle article
    article = getArticleById(publisherId, articleId)
    (contentFreq, contentFeat) = getFrequencyMatrix([article['content']], language)
    (titleFreq, titleFeat) = getFrequencyMatrix([article['title']], language)
    # Create feature: value dictionaries
    articleContentDict = {contentFeat[i]: contentFreq[i] for i in range(0, min(len(contentFeat), len(contentFreq)))}
    articleTitleDict = {titleFeat[i]: titleFreq[i] for i in range(0, min(len(titleFeat), len(titleFreq)))}

    #Handle snippets
    snippetEntities= getSnippets()
    snippetDict= snippetsScore.getScore(snippetEntities, articleContentDict, articleTitleDict)
    tagsDict= tagsScore.getTagScores(snippetEntities, articleContentDict, articleTitleDict)

    #Compile the scores into one dict
    totalDict={}
    for snippetID in tagsDict.keys():
        allScoresDict={}
        allScoresDict['tagsTextScore']= tagsDict[snippetID]['textScore']
        allScoresDict['tagsTitleScore']= tagsDict[snippetID]['titleScore']
        allScoresDict['customTextScore']= tagsDict[snippetID]['customTextScore']
        allScoresDict['customTitleScore']= tagsDict[snippetID]['customTitleScore']
        allScoresDict['snippetTextScore']= snippetDict[snippetID]['contentScore']
        allScoresDict['snippetTitleScore']= snippetDict[snippetID]['titleScore']
        totalDict[snippetID]= allScoresDict

    #Return snippet with highest overall score
    topSnippet= findTopSnippet(totalDict)

    #Only match snippet if score is above threshold
    if topSnippet['score'] > scoreThreshold:
        print(topSnippet['snippetId'])
        print(topSnippet['score'])
        return True
    return False


if __name__ == '__main__':
  #print(snippetsScore.getScore('martech.zone', 'ecommerce-shipping-options'))
  #print(tagsScore.getTagScores('martech.zone', 'ecommerce-shipping-options'))
  makeSnippetSelection('business-case-for-dam', 'martech.zone', 'en')
