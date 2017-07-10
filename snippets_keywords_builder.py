import requests as req
from newspaper import Article
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import scipy
import operator
import re
from google.cloud import datastore
import json

# Custom modules
import config

# Init
ds = datastore.Client(project=config.PROJECT_ID)

# Set env variable for keyfile - might not be necceary in production
'''
import sys,os,os.path
#sys.path.append(os.path.expanduser('~/code/eol_hsrl_python'))
#os.environ['GOOGLE_APPLICATION_CREDENTIALS']='/Users/leoliber/Repos/simoti/ad-server/keyfile.json'
#os.environ['HSRL_CONFIG']=os.path.expanduser('~/hsrl_config')
'''

def getStopWords(language):
    # Hebrew stop words from: https://github.com/stopwords-iso/stopwords-he
    stopWords = {
        'he': ["אבל","או","אולי","אותה","אותו","אותי","אותך","אותם","אותן","אותנו","אז","אחר","אחרות","אחרי","אחריכן","אחרים","אחרת","אי","איזה","איך","אין","איפה","איתה","איתו","איתי","איתך","איתכם","איתכן","איתם","איתן","איתנו","אך","אל","אלה","אלו","אם","אנחנו","אני","אס","אף","אצל","אשר","את","אתה","אתכם","אתכן","אתם","אתן","באיזומידה","באמצע","באמצעות","בגלל","בין","בלי","במידה","במקוםשבו","ברם","בשביל","בשעהש","בתוך","גם","דרך","הוא","היא","היה","היכן","היתה","היתי","הם","הן","הנה","הסיבהשבגללה","הרי","ואילו","ואת","זאת","זה","זות","יהיה","יוכל","יוכלו","יותרמדי","יכול","יכולה","יכולות","יכולים","יכל","יכלה","יכלו","יש","כאן","כאשר","כולם","כולן","כזה","כי","כיצד","כך","ככה","כל","כלל","כמו","כן","כפי","כש","לא","לאו","לאיזותכלית","לאן","לבין","לה","להיות","להם","להן","לו","לי","לכם","לכן","למה","למטה","למעלה","למקוםשבו","למרות","לנו","לעבר","לעיכן","לפיכך","לפני","מאד","מאחורי","מאיזוסיבה","מאין","מאיפה","מבלי","מבעד","מדוע","מה","מהיכן","מול","מחוץ","מי","מכאן","מכיוון","מלבד","מן","מנין","מסוגל","מעט","מעטים","מעל","מצד","מקוםבו","מתחת","מתי","נגד","נגר","נו","עד","עז","על","עלי","עליה","עליהם","עליהן","עליו","עליך","עליכם","עלינו","עם","עצמה","עצמהם","עצמהן","עצמו","עצמי","עצמם","עצמן","עצמנו","פה","רק","שוב","של","שלה","שלהם","שלהן","שלו","שלי","שלך","שלכה","שלכם","שלכן","שלנו","שם","תהיה","תחת"],
        'en': 'en'
    }
    return stopWords.get(language, 'en')

def getQueryUrls(query):
    queryUrl = 'https://www.googleapis.com/customsearch/v1?key={}&cx={}&q={}'
    res = req.get(queryUrl.format(config.SEARCHENGINE_KEY, config.SEARCHENGINE_ID, query))
    queryResults = res.json()
    urls = [item['link'] for item in queryResults['items']]
    return urls

def scrape(url, language='en'):
    page = Article(url = url, language = language)
    page.download()
    # TODO: try catch newspapaer and retry due to the 'download()' fail
    page.parse()
    return page.text

def getTopNFeatures(N, vectorizer, matrix):
    features = vectorizer.get_feature_names()
    topFeatures = {}

    for i in range(0, matrix.shape[0]):
        row = matrix.getrow(i).toarray()[0].ravel()
        topIndicies = row.argsort()[-N:]
        for j in range(0, N):
            tempFeature = features[topIndicies[j]]
            topFeatures[tempFeature] = topFeatures.get(tempFeature, 0) + row[topIndicies[j]]

    topFeatures = sorted(topFeatures.items(), key = operator.itemgetter(1), reverse=True) # Sort
    topFeatures = topFeatures[:N] # Return top N items

    return topFeatures

def getNGrams(token, articles):
    corpus = ','.join(articles)

    preBigrams = re.findall('(\\w+\\s+{})'.format(token), corpus, re.M|re.I)
    sufBigrams = re.findall('({}\\s+\\w+)'.format(token), corpus, re.M|re.I)
    preTrigrams = re.findall('(\\w+\\s+\\w+\\s+{})'.format(token), corpus, re.M|re.I)
    sufTrigram = re.findall('({}\\s+\\w+\\s+\\w+)'.format(token), corpus, re.M|re.I)

    return set(preBigrams + sufBigrams + preTrigrams + sufTrigram) # Convert to a set to remove duplciates

def getPhrases(features, articles):
    phrases = {}
    for i in range(0, len(features)):
        phrases[features[i][1]] = phrases.get(features[i][1], set()) | getNGrams(features[i][0], articles)

    return phrases

def getSnippetById(snippetId):
    snippetKey = datastore.Key('snippets', snippetId, project=config.PROJECT_ID)
    snippet = ds.get(key=snippetKey)
    return snippet

# Custom encoder for JSON converter
'''
class SetEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, set):
      return list(obj)
    return json.JSONEncoder.default(self, obj)
'''

def saveSnippetKeywords(snippet, weightedNGrams):
    # Attempt 1 - saves a JSON string - useless
    #snippet['calculatedKeywords'] = json.dumps(weightedNGrams,  cls=SetEncoder, ensure_ascii=False)

    # Attempt 2 - create an embeded entity manually
    snippet['calculatedKeywords'] = datastore.Entity(key=ds.key('calculatedKeywords'))
    for weight in weightedNGrams:
        for nGram in weightedNGrams[weight]:
            snippet['calculatedKeywords'][nGram] = weight

    ds.put(snippet)

def setSnippetWeightedKeywords(snippetId):
    snippet = getSnippetById(snippetId)
    print('Found snippet id [', snippetId, ']')

    urls = getQueryUrls(snippet['title'])
    print('Found {} search results for [{}]'.format(len(urls), snippet['title']))

    #articles = [scrape(url, snippet['language']) for url in urls]
    articles = []
    for i in range(0, len(urls)):
        try:
            articles = articles + [scrape(urls[i], snippet['language'])]
        except BaseException as e:
            print('ERROR in parsing [', urls[i], ']', str(e))
            pass

    print('Scraped {} articles'.format(len(articles)))

    if len(articles):
        # Build TF-IDF matrix
        stopWords = getStopWords(snippet['language'])
        vectorizer = TfidfVectorizer(max_df=0.5, min_df=2, stop_words = stopWords)
        TfIdfMatrix = vectorizer.fit_transform(articles)

        #features = vectorizer.get_feature_names()
        #print('Built matrix with {} features'.format(len(features)))

        topFeatures = getTopNFeatures(8, vectorizer, TfIdfMatrix)
        print('Top features are:', topFeatures)

        weightedNGrams = getPhrases(topFeatures, articles)
        print('N grams:', weightedNGrams)

        saveSnippetKeywords(snippet, weightedNGrams)


#row = TfIdfMatrix.toarray()[0]
#index = np.argmax(row)
#len(TfIdfMatrix.toarray())
#print("Most popular item is", features[index], "with value", row[index] , "at index", index, ' for ', urls[1])
#scipy.sparse.csr_matrix.max(TfIdfMatrix)

if __name__ == '__main__':
    setSnippetWeightedKeywords(5722646637445120)
