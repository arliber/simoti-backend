#!/usr/bin/env python
# coding=utf8
from sklearn.feature_extraction import stop_words
from newspaper import Article

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


def scrape(url, language='en'):
  ''' Scrape given url using supplied or default language

  Args:
    url (str): Article's URL for parsing
    language (str, optional): Language to parse in. Defaults to 'en'

  Returns:
    Parsed text if succeeds, empty string otherwise
  '''
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

  return (page.text, page.title) if success else ('','')
