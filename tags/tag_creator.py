#!/usr/bin/env python
# coding=utf8

"""Parses xml tree of tags, finds corresponding wordPouch on Twitter
    and adds these to GC datastore as tags entities"""

# Add common folder to modules path
import sys
sys.path.append('./')

import re
import config
import bs4
import tweepy
import nltk
from bs4 import BeautifulSoup as BS
from google.cloud import datastore
from nltk.probability import FreqDist
from heapq import nlargest
from collections import defaultdict
from decimal import *

from common import DAL

badTags= []     #List of tags which did not return enough entries
n= 20           #Number of top words we will save
c= .3           #Score given to selected tags


# Finds the n most relevant words and their normalized scores
def extractPouch(tag0, tag1, results, textfile):
    global n
    global c

    #Save all found hashtags in resultWords
    resultWords= []
    for line in results:
        hashtags= re.findall(r"#(\w+)", str(line))  #Find hashtags
        for ht in hashtags:
            result = re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', ht) #Separate camelCase
            resultWords.append(result)

    #Save top n words in finaldict not including chosen tags
    maxNum= 0
    finaldict= {}
    freqdist= FreqDist(resultWords)
    wordMVPs= nlargest(n, freqdist, key=freqdist.get)
    for w in wordMVPs:
        if w.lower() != tag0 and w.lower() != tag1:
            num= freqdist[w]
            if maxNum == 0:
                maxNum= num
            finaldict[w]= num

    words= []
    values= []
    wordPouch= []
    #Normalize distribution and add chosen tags with given value c
    for w in finaldict:
        wordValue= Decimal(finaldict[w]/maxNum).quantize(Decimal(10) ** -3)
        words.append(str(w))
        values.append(float(wordValue))
    words.append(tag0)
    words.append(tag1)
    values.append(c)
    values.append(c)
    wordPouch.append(words)
    wordPouch.append(values)
    return wordPouch


# Queries Twitter with given tags and calls extractPouch
def searchTwitter(tag0, tag1):
    global n
    global c

    auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
    auth.set_access_token(config.access_token, config.access_token_secret)
    api = tweepy.API(auth)

    #Create Query string
    if tag1 is None:
        query= str(tag0) + " #" + str(tag0)
    else:
        query= str(tag0) + " #" + str(tag0) + " " + str(tag1) + " #" + str(tag1)
    #print(query)        #For debugging only

    try:
        results = api.search(q=query, lang='en', result_type='mixed', count= 500)
        textfile= str(tag0) + "," + str(tag1) + ".txt"  #For debugging only
        return extractPouch(tag0, tag1, results, textfile)
    except:
        return []


def createCustomTag(tagName):
    global n
    global c

    wordPouch= searchTwitter(tagName, None)   #Retrieve Twitter wordPouch

    if len(wordPouch) == 0 or len(wordPouch[0]) < 10:
        #This is a bad tag
        return None
    else:
        #Create tag entity and save it in datastore
        #ds = datastore.Client(project= str(config.PROJECT_ID))     #Setup datastore access
        #tag_key= datastore.Key("tags", tagName, project=str(config.PROJECT_ID))
        tag_key= datastore.Key("tags", 'CUSTOM',"tags", tagName, project=config.PROJECT_ID)
        tag_ent= datastore.Entity(key= tag_key)
        tag_ent["language"]= "en"
        tag_ent["wordPouch"]= wordPouch[0]
        tag_ent["wordPouchScores"]= wordPouch[1]
        DAL.saveEntity(tag_ent)
        return tag_ent



# Recursive function to find which tags to add
# Calls searchTwitter to get wordPouch for these tags
# Adds tags and associated wordPouch to GC datastore
def createTagFromTree(parent):
    global n
    global c
    global badtags

    addParent= False    #Indicates whether parent entity should be added
    children= parent.children

    for i,child in enumerate(children):
        if i % 2 == 1:  #parent.children returns: None child None child ...
            if len(list(child.children)) is 0:
            #Invariant: Child is in deepest layer
                addParent= True
                cname= child.name
                pname= parent.name
                wordpouchchild= searchTwitter(pname, cname)   #Retrieve Twitter wordPouch

                #Handle child entity
                if len(wordpouchchild[0]) < 10:
                    #This is a bad pair of tags
                    badTag= pname + "," + cname
                    badtags.append(badTag)
                else:
                    #Create tag entity and save it in datastore
                    child_key= datastore.Key("tags", pname,"tags", cname, project=str(config.PROJECT_ID))
                    ctag_ent= datastore.Entity(key= child_key)
                    ctag_ent["language"]= "en"
                    ctag_ent["wordPouch"]= wordpouchchild[0]
                    ctag_ent["wordPouchScores"]= wordpouchchild[1]
                    DAL.saveEntity(ctag_ent)
            else:
            #Invariant: Child is not in deepest layer so we need to recurse
                createTagFromTree(child)

    if addParent:
        wordpouchparent= searchTwitter(pname, None)
        #Handle parent entity
        if len(wordpouchparent[0]) < 10:
            #This is a bad tag
            badtags.append(parent.name)
        else:
            #Create tag entity and save it in datastore
            parent_key= datastore.Key("tags", parent.name, project=str(config.PROJECT_ID))
            ptag_ent= datastore.Entity(key= parent_key)
            ptag_ent["language"]= "en"
            ptag_ent["wordPouch"]= wordpouchparent[0]
            ptag_ent["wordPouchScores"]= wordpouchparent[1]
            DAL.saveEntity(ptag_ent)


# Parse Tags.xml and call createTag to add tags entities to GC datastore
def parseXML(topTag):
    global badTags
    with open("Tags.xml") as fp:
        soup = BS(fp, "lxml")
        createTagFromTree(getattr(soup, topTag))
    return badTags

if __name__ == '__main__':
  parseXML('fashion')