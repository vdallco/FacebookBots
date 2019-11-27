# -*- coding: utf-8 -*-

# Google Translate Bot
# Cody DallaValle

# Auth token from Maximum Bots - Paintmin 
# http://maxbots.ddns.net/token/

import facebook
import random
import time
import urllib
import urllib2
import re
import time
from datetime import datetime
import json
import sys
from googletrans import Translator
import googletrans
from PIL import Image, ImageDraw, ImageFont
from html.parser import HTMLParser

authToken = 'YOUR-AUTH-TOKEN-HERE'
pageId = 'PAGE-ID'

fb = facebook.GraphAPI(access_token=authToken)
trans = googletrans.Translator()
quotesApi = 'http://quotesondesign.com/wp-json/posts?filter[orderby]=rand&filter[posts_per_page]=1'
categories = ['students', 'art', 'love', 'funny', 'life', 'sports', 'management', 'inspire']

# https://stackoverflow.com/questions/9662346/python-code-to-remove-html-tags-from-a-string
def cleanHtml(raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext

def timeStamp():
        return datetime.now().strftime('%Y.%m.%d.%H.%M.%S.%f')

def txtToPng(txt):
        img = Image.new('RGB', (800, 950), color = (42, 42, 42))
        d = ImageDraw.Draw(img)
        font = ImageFont.truetype('/Library/Fonts/Arial.ttf', 20)
        d.text((15,15), txt, font=font, fill=(255,255,255))
        fileName = timeStamp() + ".png"
        img.save(fileName)
        return fileName

def htmlUnescape(txtStr):
	h = HTMLParser()
	return h.unescape(txtStr)

def fbPost(imgFile, translateTxt):
	resp = fb.put_photo(image=open(imgFile), message=translateTxt)
	postId = resp['id']
	return postId

def randomQuote():
	src = urllib2.urlopen(quotesApi).read()
	srcObj = json.loads(src[1:-1])
	print srcObj
	return cleanHtml(srcObj['content'])

def randomLang():
	langCodes = googletrans.LANGCODES
	randLang = random.choice(langCodes.keys())
	randLangCode = langCodes[randLang]
	return randLangCode
		
def randomTranslate(txtStr):
	destLang = randomLang()
	translated = trans.translate(txtStr, destLang)
	langs = googletrans.LANGCODES
	transTxt = translated.text if not type(translated) is list else translated[0].text
	destLangTxt = langs.keys()[langs.values().index(destLang)]
	print "Translated into " + destLangTxt + ": " + transTxt
	return [destLang, htmlUnescape(transTxt), destLangTxt]
	
def randomTranslations(seedTxt):
	randRounds = random.randint(8, 24)
	currentTxt = ['', htmlUnescape(seedTxt)]
	translatorTxt = u'Starting text: ' + currentTxt[1]
	print "Starting text: " + currentTxt[1]
	for x in xrange(0, randRounds):
		currentTxt = randomTranslate(currentTxt[1])
		translatorTxt += currentTxt[2] + ": " + currentTxt[1] + '\n'

	toEnglish = trans.translate(currentTxt[1], "en")
	currentTxt = toEnglish.text if not type(toEnglish) is list else toEnglish[0].text # if there are multiple translations, just use the first
	print "Back to English: " + currentTxt 
	return [htmlUnescape(seedTxt), translatorTxt, currentTxt]

def postRandomTrans():
	translate = randomTranslations(randomQuote())
	imgFile = txtToPng(translate[1] + '\n' + translate[2])
	fbPost(imgFile, u'𝐒𝐭𝐚𝐫𝐭𝐢𝐧𝐠 𝐭𝐞𝐱𝐭: ' + translate[0] + u'\n𝐓𝐫𝐚𝐧𝐬𝐥𝐚𝐭𝐞𝐝 𝐢𝐧𝐭𝐨: ' + translate[2])

while True:
	try:
		postRandomTrans()
		timeToWait = random.randint(6*60, 17*60)
		print "Waiting " + str(timeToWait/60) + " minutes until the next post"
		time.sleep(timeToWait)
	except KeyboardInterrupt:
		sys.exit(0)
	except Exception as e:
		print str(e)
