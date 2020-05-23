# Know Your Meme Bot v1.1
# Cody DallaValle

# Auth token from Maximum Bots - Paintmin 
# http://maxbots.ddns.net/token/

# Known issues:

# Infinite loop has caused KYM to IP block me more than once... (I think fixed, now)
# memes logged in files when never actually posted

import facebook
import random
import time
import urllib
from urllib.request import urlopen
import re
import time
import json
import sys

authToken = 'YOUR_AUTH_TOKEN_HERE'
pageId = 'YOUR_PAGE_ID'

fb = facebook.GraphAPI(access_token=authToken)
kymUrl = 'https://knowyourmeme.com/random'
logFile = 'memesPosted.txt'
errorLog = 'errors.txt'

aboutSrc = '<h2 id="about">About</h2>'
overviewSrc = '<h2 id="overview">Overview</h2>'
backgroundSrc = '<h2 id=\"background">Background</h2>'
originSrc = '<h2 id="origin">Origin</h2>'
historySrc = '<h2 id="history">History</h2>'
spreadSrc = '<h2 id="spread">Spread</h2>'
viewSrc = '<dd class=\'views\' title=\''
picSrc = '<dd class=\'photos\' title=\'' # picture count
imgSrc = 'data-src="'
deadMeme = '<h6>This entry has been rejected due to incompleteness or lack of notability.</h6>'
titleSrc = 'og:title\' content=\''
urlSrc = 'og:url\' content=\''

def timeStamp():
	return time.strftime('%Y.%m.%d.%H.%M.%S')

def createAlbum(nameStr, descStr):
	path = pageId + "/albums"
	postArgs = {'access_token': authToken, 'name': nameStr, 'message': descStr}
	postData  = urllib.parse.urlencode(postArgs).encode("utf-8")
	response = urlopen("https://graph.facebook.com/" + pageId + "/albums?" , postData).read().decode('utf-8')
	id = json.loads(response)
	return id['id']

# https://stackoverflow.com/questions/9662346/python-code-to-remove-html-tags-from-a-string
def cleanHtml(raw_html):
	cleanr = re.compile('<.*?>')
	cleantext = re.sub(cleanr, '', raw_html)
	return cleantext

def pagePost(txtStr, imgUrlArr, albumId):
	for imgUrl in imgUrlArr:
		fb.put_photo(pageId, albumId + '/photos', url=imgUrl) 

def logMeme(memeTitle):
	log = open(logFile, 'a+')
	if memeTitle in log.read(): return False
	log.write('\n'+memeTitle)
	return True

def logError(errorTitle):
	log = open(errorLog, 'a')
	log.write(errorTitle + '\t' + timeStamp() + '\n')

def getPics(srcStr, imgCount):
	returnList = []

	photosUrl = srcStr.split(urlSrc)[1].split('\'')[0] + '/photos'
	srcStr = urlopen(photosUrl).read().decode('utf-8')

	loop = True
	x = 0
	while loop:
		try:
			imgUrl = srcStr.split(imgSrc)[x].split('"')[0]
			if "https://i.kym-cdn.com/photos/images" in imgUrl and "photos/images/list" not in imgUrl:
				returnList.append(imgUrl.replace('masonry', 'newsfeed'))
			x += 1
		except:
			loop = False # this is dumb, why not just count the number of eligible images first and then iterate. But it works
	return returnList

def rndSleep():
		timeSleep = random.randint(7*60, 400*60)
		timeSleepMins = timeSleep / 60
		print("Sleeping for " + str(timeSleepMins) + " minutes...")
		time.sleep(timeSleep)

def getMeme():
	desc = ''
	kymSrc = ''
	title = ''

	try:
		kymSrc = urlopen(kymUrl).read().decode('utf-8')
		print("Got KYM source...")
	except Exception as e:
		print("Error while getting KYM source..." + str(e))
		return 0

	try:
		rawTitle = kymSrc.split(titleSrc)[1].split('\' />')[0]
		print('Raw title: ' + rawTitle)
		title = cleanHtml(rawTitle)
	except Exception as e:
		print("Error while parsing title..." + str(e))
		return 0
	
	try:
		views = kymSrc.split(viewSrc)[1].split(' ')[0]
		picCount = kymSrc.split(picSrc)[1].split(' ')[0]
		
		print(title)
		print(views)
		print(picCount)
		
		if not title or not views or not picCount:
			print("Couldn't parse views, pic counts, or views...")
			rndSleep()
			getMeme()
		elif not logMeme(title): # already posted
			print("Already posted...")
			rndSleep()
			getMeme()
		elif picCount == "0":
			print("No pictures...")
			rndSleep()
			getMeme()
		elif deadMeme in kymSrc:
			desc = '[DATA EXPUNGED]'
		
			imgs = getPics(kymSrc, picCount)
			newAlbum = createAlbum(title, desc)
			pagePost(desc, imgs, newAlbum)
			print(desc)
		else:
			aboutTxt = (kymSrc.split(aboutSrc)[1].split('<h')[0] if aboutSrc in kymSrc else '')
			originTxt = (kymSrc.split(originSrc)[1].split('<h')[0] if originSrc in kymSrc else '')
			overviewTxt = (kymSrc.split(overviewSrc)[1].split('<h')[0] if overviewSrc in kymSrc else '')
			backgroundTxt = (kymSrc.split(backgroundSrc)[1].split('<h')[0] if backgroundSrc in kymSrc else '') 
			historyTxt = (kymSrc.split(historySrc)[1].split('<h')[0] if historySrc in kymSrc else '') 
			spreadTxt = (kymSrc.split(spreadSrc)[1].split('<h')[0] if spreadSrc in kymSrc else '') 
			print("Finding image urls")
			imgs = getPics(kymSrc, picCount)
			print(imgs)
			desc = cleanHtml(aboutTxt + '\n' + originTxt + '\n' + overviewTxt + '\n' + backgroundTxt + '\n' + historyTxt + '\n' + spreadTxt)
			print("Making album...")
			newAlbum = createAlbum(title, desc)
			print("Posting to Facebook with album ID  " + str(newAlbum) + "...")
			pagePost(desc, imgs, newAlbum)
			print("Posted to Facebook...")
			print(cleanHtml(aboutTxt + '\n' + originTxt + '\n' + overviewTxt + '\n' + backgroundTxt + '\n' + historyTxt + '\n' + spreadTxt))
	except Exception as e:
		print(str(e))
		print("Logging error for " + title + " at " + timeStamp())
		logError(title)

while True:
	try:
		getMeme()
		rndSleep()
	except KeyboardInterrupt:
		sys.exit(0)
	except:
		print("Unhandled exception at " + timeStamp())
		rndSleep()

