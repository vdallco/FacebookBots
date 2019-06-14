# Know Your Meme Bot v1.1
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
import json
import sys

authToken = 'YOUR-AUTH-TOKEN-HERE'
pageId = 'PAGE-ID'

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
	postData  = urllib.urlencode(postArgs)
	response = urllib2.urlopen("https://graph.facebook.com/" + pageId + "/albums?" , postData).read()
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
	srcStr = urllib2.urlopen(photosUrl).read()

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

def getMeme():
	desc = ''
	kymSrc = ''
	title = ''

	try:
		kymSrc = urllib2.urlopen(kymUrl).read()
	except Exception as e:
		print str(e)
		return 0

	try:
		title = cleanHtml(kymSrc.split(titleSrc)[1].split('\' />')[0])
	except Exception as e:
		print str(e)
		return 0
	
	try:
		views = kymSrc.split(viewSrc)[1].split(' ')[0]
		picCount = kymSrc.split(picSrc)[1].split(' ')[0]
		
		print title
		print views
		print picCount
		
		if not title or not views or not picCount:
			print "Not sure what happened here"
		elif not logMeme(title): # already posted
			getMeme()
		elif picCount == "0":
			getMeme()	
		elif deadMeme in kymSrc:
			desc = '[DATA EXPUNGED]'
		
			imgs = getPics(kymSrc, picCount)
			newAlbum = createAlbum(title, desc)
			pagePost(desc, imgs, newAlbum)
			print desc
		else:
			aboutTxt = (kymSrc.split(aboutSrc)[1].split('<h')[0] if aboutSrc in kymSrc else '')
			originTxt = (kymSrc.split(originSrc)[1].split('<h')[0] if originSrc in kymSrc else '')
			overviewTxt = (kymSrc.split(overviewSrc)[1].split('<h')[0] if overviewSrc in kymSrc else '')
			backgroundTxt = (kymSrc.split(backgroundSrc)[1].split('<h')[0] if backgroundSrc in kymSrc else '') 
			historyTxt = (kymSrc.split(historySrc)[1].split('<h')[0] if historySrc in kymSrc else '') 
			spreadTxt = (kymSrc.split(spreadSrc)[1].split('<h')[0] if spreadSrc in kymSrc else '') 
			imgs = getPics(kymSrc, picCount)
			desc = cleanHtml(aboutTxt + '\n' + originTxt + '\n' + overviewTxt + '\n' + backgroundTxt + '\n' + historyTxt + '\n' + spreadTxt)
			newAlbum = createAlbum(title, desc)
			pagePost(desc, imgs, newAlbum)
			print cleanHtml(aboutTxt + '\n' + originTxt + '\n' + overviewTxt + '\n' + backgroundTxt + '\n' + historyTxt + '\n' + spreadTxt)
	except:
		print "Logging error for " + errorRef + " at " + timeStamp()
		logError(title)

while True:
	try:
		getMeme()
		time.sleep(random.randint(7*60, 15*60))
	except KeyboardInterrupt:
		sys.exit(0)
	except:
		print "Unhandled exception at " + timeStamp()

