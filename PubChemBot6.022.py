# PubChemBot 6.022
# Cody DallaValle

# Auth token from Maximum Bots - Paintmin
# http://maxbots.ddns.net/token/

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
pcUrl = 'https://pubchem.ncbi.nlm.nih.gov/'
errorLog = 'errors.txt' # todo: error logging

def rndSleep():
		timeSleep = random.randint(7*60, 400*60)
		timeSleepMins = timeSleep / 60
		print("Sleeping for " + str(timeSleepMins) + " minutes...")
		time.sleep(timeSleep)
        
def getImgUrl(compoundId):
	return pcUrl + 'rest/pug/compound/cid/' + compoundId + '/PNG'

def getFormula(compoundId):
	src = urlopen(pcUrl + 'rest/pug/compound/cid/' + compoundId + '/property/MolecularFormula,IUPACName/JSON').read().decode('utf-8')
	srcJson = json.loads(src)
	return "Molecular formula: " + srcJson["PropertyTable"]["Properties"][0]["MolecularFormula"] + "\nName: " + srcJson["PropertyTable"]["Properties"][0]["IUPACName"]

def getSynonyms(compoundId):
	try:
		src = urlopen(pcUrl + 'rest/pug/compound/cid/' + compoundId + '/Synonyms/JSON').read().decode('utf-8')
		srcJson = json.loads(src)
		return srcJson["InformationList"]["Information"][0]["Synonym"]
	except:
		return 0

def randomCompound():
	cid = str(random.randint(1, 90000000))
	imgUrl = getImgUrl(cid)
	formula = getFormula(cid)
	names = getSynonyms(cid)
	if names == 0: return randomCompound()
	try:
		namesList = '\n'.join(names)
		desc = formula + '\nSynonyms:\n ' + namesList
		print(formula + '\n' + imgUrl + '\n' + namesList)
		graphPost(imgUrl, desc, cid)
	except Exception as e:
		print(str(e))
		


def graphPost(imgUrl, desc, cid):
	try:
		print("Trying to post to Facebook...")
		resp = fb.put_object(pageId, "photos", url=imgUrl, caption=desc)
		print("Posted to Facebook, making comments...")
		postId = resp['id']
		fb.put_object(postId, "comments/comments", message=pcUrl + "compound/" + cid)
	except Exception as e:
		print("Error during Graph post.." + str(e))

while True:
	try:
		randomCompound()
		rndSleep()
	except KeyboardInterrupt:
		sys.exit()
	except Exception as e:
		print("Error: \n" + str(e))
		rndSleep()
