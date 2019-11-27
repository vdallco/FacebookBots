# -*- coding: utf-8 -*-

# LyricsBot1985
# Cody DallaValle

# Auth token from Maximum Bots - Paintmin 
# http://maxbots.ddns.net/token/

import facebook
import random
from datetime import datetime
import requests
import re
import time
import json
import sys
from PIL import Image, ImageDraw, ImageFont
import time

authToken = 'YOUR-AUTH-TOKEN-HERE'
pageId = 'PAGE-ID'

minSongs = 2
maxSongs = 7
minLines = 1
maxLines = 4

fb = facebook.GraphAPI(access_token=authToken)

def timeStamp():
        return datetime.now().strftime('%Y.%m.%d.%H.%M.%S.%f')		

def randomLines(lyrics, lyricId):
	lines = lyrics.splitlines()
	linesMax = len(lines) - 1
	subLyricStart = random.randint(0, linesMax - maxLines)
	subLyricEnd = random.randint(subLyricStart + minLines, subLyricStart + maxLines)
	
	subLyric = ''
	for x in xrange(subLyricStart, subLyricEnd):
		if lines[x]:
			subLyric += '\n' + lines[x]
	if not subLyric: return randomLines(lyrics, lyricId)
	return subLyric + "(" + str(lyricId) + ")"

def randomLyrics(lyricId):
	rndInt = random.randint(1, 3583)
	response = requests.get("https://musicdemons.com/api/v1/song/" + str(rndInt), headers={"with":"lyrics"})
	try:
		respObj = response.json()
		songTitle = respObj['title']
		songYtID = respObj['youtube_id']
		songLyrics = respObj['lyrics'][0]['lyrics']
		print songTitle + '\n'
		newLyric = randomLines(songLyrics, lyricId)
		return [songTitle, newLyric, songYtID]
	except Exception as e:
		return randomLyrics(lyricId) # mulligan?

def txtToPng(txt):
        img = Image.new('RGB', (600, 450), color = (42, 42, 42))
        d = ImageDraw.Draw(img)
	font = ImageFont.truetype('/Library/Fonts/Arial.ttf', 20)
        d.text((25,25), txt, font=font, fill=(255,255,255))
	fileName = timeStamp() + ".png"
        img.save(fileName)
	return fileName

def fbPost(imgFile, songsUsed, ytLinks):
	resp = fb.put_photo(image=open(imgFile), message=songsUsed)
	postId = resp['id']
	for ytLink in ytLinks:
		fb.put_object(postId, "comments/comments", message="https://www.youtube.com/watch?v=" + ytLink)

def randomSong():
	numChildSongs = random.randint(minSongs, maxSongs)
	lyricCount = 1
	youtubeIds = []
	titles = 'Songs used: '
	song = ''
	for x in xrange(0, numChildSongs):
		try:
			genLyrics = randomLyrics(lyricCount)
			if genLyrics is None: continue
			titles += genLyrics[0] + '(' + str(x+1) + '), '
			song += genLyrics[1]
			youtubeIds.append(genLyrics[2])
			lyricCount += 1
		except Exception as e:
			print str(e)

	imgFile = txtToPng(song)
	fbPost(imgFile, titles[:-2], youtubeIds)
	print titles[:-2]
	print song

while True:
	while True:
		try:
			randomSong()
			waitTime = random.randint(5*60, 13*60)
			print "Next post in  " + str(waitTime/60) + " minutes"
			time.sleep(waitTime)
		except KeyboardInterrupt:
			sys.exit()
		except Exception as e:
			print str(e)
