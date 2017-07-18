#!/usr/bin/env python
# coding=utf8

import charlie.snippetsScore

# Add tags folder to modules path
import sys
sys.path.append('./')
sys.path.append('../')

from tags import tagsScore

'''
  Run snippet scrore
  Run tags based score
  Apply predefined weights
  If score above predefined treshold - call compiler with article and selected snippet id

  IMPORTANT: Log, a lot
'''

tagsTextWeight= 1
tagsTitleWeight= 1
customTextWeight= 1
customTitleWeight= 1
articlesTextWeight= 1
articlesTitleWeight= 1


def computeFinalScores(articleId, publisherId, language):

    global tagsTextWeight
    global tagsTitleWeight
    global customTextWeight
    global customTitleWeight
    global articlesTextWeight
    global articlesTitleWeight

    snippetDict= snippetsScore.getScore(publisherId, articleId, language)
    tagsDict= tagsScore.getTagScores(publisherId, articleId, language)
    #TODO: What if snippets change between calls?

    totalDict={}
    for snippetID in tagDict.keys:
        allScoresDict={}
        allScoresDict['tagsTextScore']= tagsDict[snippetID]['textScore']
        allScoresDict['tagsTitleScore']= tagsDict[snippetID]['titleScore']
        allScoresDict['customTextScore']= tagsDict[snippetID]['customTextScore']
        allScoresDict['customTitleScore']= tagsDict[snippetID]['customTitleScore']
        allScoresDict['articlesTextScore']= snippetDict[snippetID]['']
        allScoresDict['articlesTitleScore']= snippetDict[snippetID]['']

        totalDict[snippetID]= allScoresDict



    return False

if __name__ == '__main__':
  print(snippetsScore.getScore('martech.zone', 'ecommerce-shipping-options'))
  print(tagsScore.getTagScores('martech.zone', 'ecommerce-shipping-options'))
