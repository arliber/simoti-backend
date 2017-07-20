#!/usr/bin/env python
# coding=utf8

# Add common folder to modules path
import sys
sys.path.append('./')
sys.path.append('../')

# Custom modules
from common.DAL import retrievePouches


# Returns tags for all active snippets
# tagsArray[i] contains an array of tags for the i'th snippet
def retrieveTags(snippets):
    snipIDs=[]
    tagsArray=[]    #Each bin holds a taglist array of tag words
    for snip in snippets:
        taglist=[]      #Each bin holds a tag
        tags= snip['tags']
        for tag in tags:
            taglist.append(str(tag))
        snipIDs.append(snip.key.id)
        tagsArray.append(taglist)
    return (tagsArray, snipIDs)


def getTagScores(snippets, articleDict, titleDict):

    # Compute score for each snippet based on tags
    snippetScores=[]
    (tagsArray, snipIDs)= retrieveTags(snippets)
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
        #as well as the words which contributed to the score if
        #at least one of the four scores is nonzero
        if currentSnippetScore > 0 or currentTitleScore > 0 or currentCustomScore > 0 or currentCustomTitleScore > 0:
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
