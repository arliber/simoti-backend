#!/usr/bin/env python
# coding=utf8

import requests as req
from newspaper import Article
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import scipy
import operator
import re
from google.cloud import datastore
import json
from sklearn.feature_extraction import stop_words

# Custom modules
import config

# Init
ds = datastore.Client(project=config.PROJECT_ID)

def getStopWords(language):
  ''' Get explicit stop words by lanauge

  Args:
    lanaguage (str): 2 characters language name
  
  Returns:
    lanaguage parameter if not found in lookup
    else returns a list of stop words
  '''

  # Hebrew stop words from: https://github.com/stopwords-iso/stopwords-he
  stopWords = {
    'he': ["אבל","או","אולי","אותה","אותו","אותי","אותך","אותם","אותן","אותנו","אז","אחר","אחרות","אחרי","אחריכן","אחרים","אחרת","אי","איזה","איך","אין","איפה","איתה","איתו","איתי","איתך","איתכם","איתכן","איתם","איתן","איתנו","אך","אל","אלה","אלו","אם","אנחנו","אני","אס","אף","אצל","אשר","את","אתה","אתכם","אתכן","אתם","אתן","באיזומידה","באמצע","באמצעות","בגלל","בין","בלי","במידה","במקוםשבו","ברם","בשביל","בשעהש","בתוך","גם","דרך","הוא","היא","היה","היכן","היתה","היתי","הם","הן","הנה","הסיבהשבגללה","הרי","ואילו","ואת","זאת","זה","זות","יהיה","יוכל","יוכלו","יותרמדי","יכול","יכולה","יכולות","יכולים","יכל","יכלה","יכלו","יש","כאן","כאשר","כולם","כולן","כזה","כי","כיצד","כך","ככה","כל","כלל","כמו","כן","כפי","כש","לא","לאו","לאיזותכלית","לאן","לבין","לה","להיות","להם","להן","לו","לי","לכם","לכן","למה","למטה","למעלה","למקוםשבו","למרות","לנו","לעבר","לעיכן","לפיכך","לפני","מאד","מאחורי","מאיזוסיבה","מאין","מאיפה","מבלי","מבעד","מדוע","מה","מהיכן","מול","מחוץ","מי","מכאן","מכיוון","מלבד","מן","מנין","מסוגל","מעט","מעטים","מעל","מצד","מקוםבו","מתחת","מתי","נגד","נגר","נו","עד","עז","על","עלי","עליה","עליהם","עליהן","עליו","עליך","עליכם","עלינו","עם","עצמה","עצמהם","עצמהן","עצמו","עצמי","עצמם","עצמן","עצמנו","פה","רק","שוב","של","שלה","שלהם","שלהן","שלו","שלי","שלך","שלכה","שלכם","שלכן","שלנו","שם","תהיה","תחת"],
    'en': list(stop_words.ENGLISH_STOP_WORDS)
  }
  return stopWords.get(language, 'english') # return specified lanauge if no not found in lookup

def getQueryUrls(query, language = 'en'):
  ''' Get a list of results URLs for the specified query, using Google Custome Engine

  Args:
    query (str): A query to search google for
  
  Returns:
    A list of all results links
  '''
  queryUrl = 'https://www.googleapis.com/customsearch/v1?key={}&cx={}&q={}'
  res = req.get(queryUrl.format(config.SEARCHENGINES[language]['key'], config.SEARCHENGINES[language]['id'], query))
  queryResults = res.json()
  urls = [item['link'] for item in queryResults['items']]
  return urls

def scrape(url, language='en'):
  ''' Scrape given url using supplied or default language

  Args:
    url (str): Article's URL for parsing
    language (str, optional): Language to parse in. Defaults to 'en'

  Returns:
    Parsed text if succeeds, empty string otherwise
  '''
  print('scrape: Scraping url ', url)
  page = Article(url = url, language = language)
  attempts = 0
  success = False
  # Exception raised following this bug: https://github.com/codelucas/newspaper/issues/357
  while(attempts < 4):
      try:
          attempts += 1
          page.download()
          page.parse()
          success = True
          break
      except BaseException as e:
          print('Error in parsing {}, attempt #{}'.format(url, attempts) , str(e))
          pass

  return page.text if success else ''

def getTopNFeatures(vectorizer, matrix):
  ''' Get to N features from the sparse TF-IDF matrix

  Args:
    N (int): Amount of features to return
    vectorizer (TfidfVectorizer): TfidfVectorizer
    matrix (Sparse matrix): TF-IDF scores

  Returns:
    Top N features with their weights
  '''
  features = vectorizer.get_feature_names()
  topFeatures = {}

  for i in range(0, matrix.shape[0]):
      row = matrix.getrow(i).toarray()[0].ravel()
      topIndicies = row.argsort()
      for j in range(0, matrix.shape[1]):
          tempFeature = features[topIndicies[j]]
          topFeatures[tempFeature] = topFeatures.get(tempFeature, 0) + row[topIndicies[j]]

  topFeatures = sorted(topFeatures.items(), key = operator.itemgetter(1), reverse=True) # Sort
  return topFeatures

def getNGrams(word, articles, language='en'):
  ''' Get bigrams and trigrams from articles based on supplied word

  Args:
    word (str): The word to base the N-Grams of of
    articles (list of strings): All articles texts

  Returns:
    A set of all bigrams and trigrams in articles
  '''
  corpus = ','.join(articles)

  preBigrams = re.findall('(\\w+\\s+{})'.format(word), corpus, re.M|re.I)
  sufBigrams = re.findall('({}\\s+\\w+)'.format(word), corpus, re.M|re.I)
  preTrigrams = re.findall('(\\w+\\s+\\w+\\s+{})'.format(word), corpus, re.M|re.I)
  sufTrigram = re.findall('({}\\s+\\w+\\s+\\w+)'.format(word), corpus, re.M|re.I)

  nGrams = set(preBigrams + sufBigrams + preTrigrams + sufTrigram)
  nGrams = [ngram for ngram in nGrams if re.findall('(\\w+)', ngram, re.M|re.I)[-1] not in getStopWords(language)]
  nGrams = [ngram for ngram in nGrams if re.findall('(\\w+)', ngram, re.M|re.I)[0] not in getStopWords(language)]

  return set(nGrams) # Convert to a set to remove duplciates

def getPhrases(features, articles, language='en'):
  ''' Get a dictionary of frequency and ngrams

  Args:
    features (list): All features
    articles (list): A list of all scraped articles

  Returns:
    A dictionary of weights and N-Grams
  '''
  phrases = {}
  for i in range(0, len(features)):
      phrases[features[i][1]] = phrases.get(features[i][1], set()) | getNGrams(features[i][0], articles, language)

  return phrases

def getSnippetById(snippetId):
  ''' Get a snippet by id from Datastore

  Args:
    snippetId (int): Snippet ID

  Returns:
    Snippet entity
  '''
  snippetKey = datastore.Key('snippets', snippetId, project=config.PROJECT_ID)
  snippet = ds.get(key=snippetKey)
  return snippet

def saveSnippetKeywords(snippet, weightedNGrams):
  ''' Save snippet N-Gram 

  Args:
    snippet (entity): Snippet entity to udpate
    weightedNGrams (dictionary): Dicionary of weight and N-Grams
  '''

  ''' # Save as an embedded entity
  snippet['calculatedKeywords'] = datastore.Entity(key=ds.key('calculatedKeywords'))
  for weight in weightedNGrams:
      for nGram in weightedNGrams[weight]:
          snippet['calculatedKeywords'][nGram] = weight '''

  # Save as two seperate fields
  snippet['wordPouch'] = []
  snippet['wordPouchScores'] = []
  for weight in weightedNGrams:
    for nGram in weightedNGrams[weight]:
      snippet['wordPouch'] = snippet['wordPouch'] + [nGram]
      snippet['wordPouchScores'] = snippet['wordPouchScores'] + [weight]
  
  ds.put(snippet)


def resultSummary(weightedNGrams, snippetId):
  ''' Returns a user-firlendly summary of of the process

  Args:
    weightedNGrams (dictionary): Dicionary of weight and N-Grams
    snippetId (int): Snippet ID
  
  Returns:
    String with summary
  '''
  ngramsCount = [len(weightedNGrams[k]) for k in list(weightedNGrams.keys())]
  return 'Saved {} N-Grams based on {} top words for snippet {}'.format(
      sum(ngramsCount),
      len(weightedNGrams),
      snippetId)

def inspectMatrix(TfIdfMatrix, vectorizer):
  features = vectorizer.get_feature_names()
  print('Built matrix with {} features: '.format(len(features)), features)
  
  row = TfIdfMatrix.toarray()[0]
  index = np.argmax(row)
  
  print('Matrix shape: ', TfIdfMatrix.shape)
  print('Most popular item is', features[index], 'with value', row[index] , 'at index', index)


def setSnippetWeightedKeywords(snippetId):
  ''' Find, weight and save related bigrams and trigrams for selected snipept

  Args:
    snippetId (int): Snippet ID
  
  Returns:
    String summary of the process
  '''
  snippet = getSnippetById(snippetId)
  print('Found snippet id [', snippetId, ']')

  urls = getQueryUrls(snippet['title'], snippet['language'])
  print('Found {} search results for [{}]'.format(len(urls), snippet['title']))
  print(urls)

  articles = [scrape(url, snippet['language']) for url in urls if not re.compile(r'\.pdf$', re.M|re.I).search(url)]
  print('Scraped {} articles'.format(len(articles)))

  if len(articles):
      # Build TF-IDF matrix
      stopWords = getStopWords(snippet['language'])
      vectorizer = TfidfVectorizer(max_df=0.5, 
                                   min_df=0.1, 
                                   ngram_range=(1, 3),
                                   lowercase=True,
                                   max_features=10,
                                   stop_words = stopWords)
      TfIdfMatrix = vectorizer.fit_transform(articles)

      inspectMatrix(TfIdfMatrix, vectorizer)

      topFeatures = getTopNFeatures(vectorizer, TfIdfMatrix)
      print('Top features are:', topFeatures)

      topFeaturesNormalized = [(feature[0],feature[1]/topFeatures[0][1]) for feature in topFeatures]
      print('Top features normazlied:', topFeaturesNormalized)

      weightedNGrams = getPhrases(topFeaturesNormalized, articles, snippet['language'])
      # print('N grams:', weightedNGrams)

      saveSnippetKeywords(snippet, weightedNGrams)

      return resultSummary(weightedNGrams, snippetId)
  else:
      return 'no relevant articles found'

# Exectue if run independantly
if __name__ == '__main__':
  print(setSnippetWeightedKeywords(5091364022779904))
