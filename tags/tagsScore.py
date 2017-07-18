#!/usr/bin/env python
# coding=utf8

# Add common folder to modules path
import sys
sys.path.append('./')
sys.path.append('../')

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction import stop_words
import numpy as np

# Custom modules
from common.DAL import getSnippets, retrievePouches, getArticleById


#Create tf matrix for an article
def getFrequencyMatrix(article, language='en'):
  stopWords = getStopWords(language)
  vectorizer = TfidfVectorizer(ngram_range=(1, 3),
                                  lowercase=True,
                                  max_features=None,
                                  stop_words = stopWords)
  TfIdfMatrix = vectorizer.fit_transform(article)
  return (TfIdfMatrix.toarray()[0], vectorizer.get_feature_names())


# Returns tags for all active snippets
# tagsArray[i] contains an array of tags for the i'th snippet
def retrieveTags():
    snipIDs=[]
    tagsArray=[]    #Each bin holds a taglist array of tag words
    snippets = getSnippets()
    for snip in snippets:
        taglist=[]      #Each bin holds a tag
        tags= snip['tags']
        for tag in tags:
            taglist.append(str(tag))
        snipIDs.append(snip.key.id)
        tagsArray.append(taglist)
    return (tagsArray, snipIDs)


def getTagScores(publisherId, articleId, lang):

    # Create dictionaries from article entity
    article = getArticleById(publisherId, articleId)
    articleTitle= article['title']
    (freq, feat) = getFrequencyMatrix([article['content']], lang)
    (tfreq, tfeat) = getFrequencyMatrix([article['content']], lang)
    articleDict = {feat[i]: freq[i] for i in range(0, min(len(feat), len(freq)))}
    titleDict = {tfeat[i]: tfreq[i] for i in range(0, min(len(tfeat), len(tfreq)))}

    # Compute score for each snippet based on tags
    snippetScores=[]
    (tagsArray, snipIDs)= retrieveTags()
    for taglist in tagsArray:
        #Iterating through snippets

        currentCustomTitleScore= 0
        currentSnippetScore= 0
        currentCustomScore= 0
        currentTitleScore= 0
        commonWords= []

        (snippetPouchArray, customPouchArray) = retrievePouches(taglist)

        for pouch in snippetPouchArray:
            #Iterating through tags for given snippet
            for word in pouch:
                #Iterating through related words for given tag
                wordScore= pouch[word] * articleDict.get(word, 0)
                titleScore= pouch[word] * titleDict.get(word, 0)
                if wordScore > 0 or titleScore > 0:
                    commonWords.append(word)
                    currentSnippetScore+= wordScore
                    currentTitleScore+= titleScore

        for cpouch in customPouchArray:
            #Iterating through custom tags for given snippet
            for cword in cpouch:
                #Iterating through related words for given custom tag
                cwordScore= cpouch[cword] * articleDict.get(cword, 0)
                ctitleScore= cpouch[cword] * titleDict.get(cword, 0)
                if cwordScore > 0 or ctitleScore > 0:
                    commonWords.append(cword + ' (custom)')
                    currentCustomScore+= cwordScore
                    currentCustomTitleScore+= ctitleScore

        #Save the four different scores for the current snippet
        #as well as the words which contributed to the score
        snippetDict={}
        snippetDict['textScore']= currentSnippetScore
        snippetDict['titleScore']= currentTitleScore
        snippetDict['customTextScore']= currentCustomScore
        snippetDict['customTitleScore']= currentCustomTitleScore
        snippetDict['commonWords']= commonWords
        snippetScores.append(snippetDict)

    #Create dictionary such that:
    #key: snippet ID
    #value:  dictionary of scores and common words
    scoreDict={}
    for j,snipScore in enumerate(snippetScores):
        scoreDict[snipIDs[j]]= snipScore
    return scoreDict


if __name__ == '__main__':
  print(getTagScores('martech.zone', 'randy-stocklin-ecommerce','en'))
