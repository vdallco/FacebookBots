# PubChemBot 6.022
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

authToken = 'YOUR-FB-GRAPH-AUTH-TOKEN-HERE'
pageId = 'PAGE-ID'

fb = facebook.GraphAPI(access_token=authToken)
pcUrl = 'https://pubchem.ncbi.nlm.nih.gov/'
errorLog = 'errors.txt' # todo: error logging

def getImgUrl(compoundId):
	return pcUrl + 'rest/pug/compound/cid/' + compoundId + '/PNG'

def getFormula(compoundId):
	src = urllib2.urlopen(pcUrl + 'rest/pug/compound/cid/' + compoundId + '/property/MolecularFormula,IUPACName/JSON').read()
	srcJson = json.loads(src)
	return "Molecular formula: " + srcJson["PropertyTable"]["Properties"][0]["MolecularFormula"] + "\nName: " + srcJson["PropertyTable"]["Properties"][0]["IUPACName"]

def getSynonyms(compoundId):
	try:
		src = urllib2.urlopen(pcUrl + 'rest/pug/compound/cid/' + compoundId + '/Synonyms/JSON').read()
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
		print formula + '\n' + imgUrl + '\n' + namesList
		graphPost(imgUrl, desc, cid)
	except Exception as e:
		print str(e)
		


def graphPost(imgUrl, desc, cid):
	resp = fb.put_object(pageId, "photos", url=imgUrl, caption=desc)
	postId = resp['id']
	fb.put_object(postId, "comments/comments", message=pcUrl + "compound/" + cid)

while True:
	try:
		randomCompound()
		time.sleep(random.randint(4*60, 18*60))
	except KeyboardInterrupt:
		sys.exit()
	except Exception as e:
		print "Error: \n" + str(e)
