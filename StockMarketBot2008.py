# Stock Market Bot 2008
# Cody DallaValle

# Auth token from Maximum Bots - Paintmin 
# http://maxbots.ddns.net/token/

import facebook
import random
import requests
from datetime import datetime
from datetime import timedelta
import yfinance as yf
import time
import json
from PIL import Image, ImageDraw, ImageFont
import sqlite3
from sqlite3 import Error
import os
import pytz
import sched
from unsplash.api import Api
from unsplash.auth import Auth

def log(txt):
    print(str(datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')) + ": " + msg)

##### Unsplash API stuff

redirect_uri = ""
code = ""

client_id = "YOUR_CLIENT_ID_HERE"
client_secret = "YOUR_CLIENT_SECRET_HERE"
 
auth = Auth(client_id, client_secret, redirect_uri, code=code)
api = Api(auth)

def getRandomImgUrl(q):
    p = api.photo.random(query=q) # returns a single element in a list
    return p[0].urls.raw

########################



##### sqlite database stuff

usersTable = """CREATE TABLE IF NOT EXISTS Users (
                                        UserId integer PRIMARY KEY AUTOINCREMENT,
                                        Name text NOT NULL,
                                        StartedPlaying text,
                                        Cash real DEFAULT 10000
                                    );"""
                                    
fbUsersTable = """CREATE TABLE IF NOT EXISTS FBUsers (
                                        FBUserId integer PRIMARY KEY AUTOINCREMENT,
                                        FBUserTxt text NOT NULL,
                                        UserId integer
                                    );"""

sharesTable= """CREATE TABLE IF NOT EXISTS UserShares (
                                        ShareId integer PRIMARY KEY AUTOINCREMENT,
                                        UserId int NOT NULL,
                                        Symbol text,
                                        Quantity int DEFAULT 10000
                                    );"""
                                    
commentsTable= """CREATE TABLE IF NOT EXISTS Comments (
                                        CommentId integer PRIMARY KEY AUTOINCREMENT,
                                        FBUserTxt text NOT NULL,
                                        Message text,
                                        FBCommentTxt text,
                                        Created text
                                    );"""

def initConnection(databaseFile):
    conn = None
    try:
        conn = sqlite3.connect(databaseFile)
        
        createUsersTbl(conn)
        createUserSharesTbl(conn)
        
        return conn
    except Error as e:
        log("Error: " + str(e))
    return conn
    
def execSQL(sqlCon, sqlStr):
    try:
        conn = sqlCon.cursor()
        result = conn.execute(sqlStr)
        return result
    except Error as e:
        log("Error: " + str(e))

def createUsersTbl(sqlCon):
    try:
        execSQL(sqlCon, usersTable) # creates the Users table if it doesn't exist
        execSQL(sqlCon, fbUsersTable) # creates the FBUsers table if it doesn't exist
        execSQL(sqlCon, commentsTable) # creates the FBUsers table if it doesn't exist
    except Error as e:
        log("Error: " + str(e))
        
def createUserSharesTbl(sqlCon):
    try:
        execSQL(sqlCon, sharesTable) # creates the UserShares table if it doesn't exist
    except Error as e:
        log("Error: " + str(e))

sqlCon = initConnection(os.getcwd() + "\sqlite.db") # make/use the sqlite DB file in the working directory

def userInit(fbUserId, name): # creares a new user record if needed and returns user info
    try:
        conn = sqlCon.cursor()
        results = conn.execute("SELECT COUNT(*) FROM FBUsers fbu JOIN Users u ON u.UserId = fbu.UserId WHERE FBUserTxt = '" + fbUserId + "'")
        
        result = conn.fetchone()[0]
        
        if result == 0: # INSERT into User and FBUser for new user
            log("Inserting new user...")
            execSQL(sqlCon, "INSERT INTO Users (Name, StartedPlaying, Cash) VALUES ('" + name + "', date('now'), 10000)")
            sqlCon.commit()
            execSQL(sqlCon, "INSERT INTO FBUsers (FBUserTxt, UserId) VALUES ('" + fbUserId + "', last_insert_rowid())")
            sqlCon.commit()
            results = conn.execute("SELECT * FROM FBUsers fbu JOIN Users u ON u.UserId = fbu.UserId WHERE FBUserTxt = '" + fbUserId + "'")
        else:
            results = conn.execute("SELECT * FROM FBUsers fbu JOIN Users u ON u.UserId = fbu.UserId WHERE FBUserTxt = '" + fbUserId + "'")
        
        # now result shouldn't ever be None
        for row in results:
            return (row[4], row[5], row[6]) # TO-DO - Return stock info when implemented
    except Error as e:
        log("Error: " + str(e))
        
        

def addComment(commentId, userId, msg, created): 
    conn = sqlCon.cursor()
    conn.execute("SELECT * FROM Comments WHERE FBCommentTxt = '" + commentId + "'")
    
    res = conn.fetchone()
    
    if res is None: return True
    
    return False # comment already processed
    
def markCommentProcessed(commentId, userId, msg, created):
    conn = sqlCon.cursor()
    conn.execute("SELECT COUNT(*) FROM Comments WHERE FBCommentTxt = '" + commentId + "'")
    
    result = conn.fetchone()
    
    if result is None:
        return # comment already marked processed
    
    execSQL(sqlCon, "INSERT INTO Comments (FBUserTxt, Message, FBCommentTxt, Created) VALUES ('" + userId + "', '" + msg + "', '" + commentId + "', '" + created + "')")
    sqlCon.commit()
    return
    
def takeUserCash(userId, cashToTake): # returns True if successful
    conn = sqlCon.cursor()
    conn.execute("SELECT Cash, u.UserId FROM Users u JOIN FBUsers fbu ON u.UserId = fbu.UserId WHERE FBUserTxt = '" + userId + "'")
    
    results = conn.fetchone()
    
    result, dbUserId = results[0], results[1]
    
    if result is None or result < cashToTake:
        return False # not enough cash or error looking it up
    
    execSQL(sqlCon, "UPDATE Users SET Cash = " + str(result - cashToTake) + " WHERE UserId = " + str(dbUserId) )
    sqlCon.commit()
    return True
    
def giveUserCash(userId, cashToGive):
    conn = sqlCon.cursor()
    conn.execute("SELECT Cash, u.UserId FROM Users u JOIN FBUsers fbu ON u.UserId = fbu.UserId WHERE FBUserTxt = '" + userId + "'")
    
    results = conn.fetchone()
    
    result, dbUserId = results[0], results[1]
    
    if result is None:
        return False # user account net yet setup? Might want to log this
    
    execSQL(sqlCon, "UPDATE Users SET Cash = " + str(result + cashToGive) + " WHERE UserId = " + str(dbUserId) )
    sqlCon.commit()
    return True

    
def insertUserShares(userId, symbol, quantity):
    conn = sqlCon.cursor()
    conn.execute("SELECT SUM(Quantity) FROM UserShares WHERE UserId = '" + userId + "' AND Symbol = '" + symbol + "'") ### *** IMPORTANT: Column name is UserId but it's really FBUserID. 
    
    results = conn.fetchone()[0]
    
    if results is None: # users first time buying this symbol
        execSQL(sqlCon, "INSERT INTO UserShares (UserId, Symbol, Quantity) VALUES ('" + userId + "', '" + symbol + "', " + str(quantity) + ")")
    else:
        execSQL(sqlCon, "UPDATE UserShares SET Quantity = " + str(int(results) + int(quantity)) + " WHERE UserId = '" + userId + "' AND Symbol = '" + symbol + "'"  )
    sqlCon.commit()
    
def deleteUserShares(userId, symbol, quantity):
    conn = sqlCon.cursor()
    conn.execute("SELECT SUM(Quantity) FROM UserShares WHERE UserId = '" + userId + "' AND Symbol = '" + symbol + "'") ### *** IMPORTANT: Column name is UserId but it's really FBUserID. 
    
    results = conn.fetchone()[0]
    
    if results is None: # users can't sell what he doesn't have
        return False
    else:
        execSQL(sqlCon, "UPDATE UserShares SET Quantity = " + str(int(results) - int(quantity)) + " WHERE UserId = '" + userId + "' AND Symbol = '" + symbol + "'"  )
        sqlCon.commit()
        return True
    
def userShares (userId, symbol):
    conn = sqlCon.cursor()
    conn.execute("SELECT Quantity FROM UserShares u WHERE UserId = '" + userId + "' AND Symbol = '" + symbol + "'")
    
    resultsRow = conn.fetchone()
    
    if resultsRow is None: return 0 # No record in UserShares means no shares
    
    results = resultsRow[0]
    
    return results
    
###########################


##### Yahoo Finance helper function

def getPrice(symbol): # gets most recent close price from Yahoo Finance or -1 if error (NOT LIVE PRICES)
    try:
        now = datetime.now()
        nowStr = now.strftime('%Y-%m-%d')
        fiveDaysAgo = now + timedelta(days=-5)
        fiveDaysAgoStr = fiveDaysAgo.strftime('%Y-%m-%d')
        data = yf.download(symbol, start=fiveDaysAgoStr, end=nowStr) # date range from 5 days ago to today (works on Sundays and long stock exchage holidays)
        return data['Close'][-1] # last element in the list is the latest close price
    except: return -1
###################################


##### Facebook Graph API stuff

AUTH_ID = 'EAACVS6jUj0QBAHKLSRJYjE03kzY3di8a6PfL7o7aUmN7TFzsMlgt1gvQX4VETYZAcEyrSQoP0ccb4JhCRYbDr3SFW5uGT2rcK6dckZA2nTplWszaS19nnNeseAz2D3uhcqELhogZBfpZAVKXiHIkbfVmJa2ppxNDhzmHIBoDtwZDZD'
PAGE_ID = '366024844032011'

fb = facebook.GraphAPI(access_token=AUTH_ID)

marketOpenImg = "marketOpen.png"
marketOpenTxt = """
The market is now open! See the list of possible actions below:

!buy [quantity] [symbol]
!sell [quantity] [symbol]
!status
!price [symbol]
"""

tryAgainMsgs = ["Please try again..", "Invalid command", "Does not compute!", "Try again with this format: !sell 400 APPL", "*90's dial-up sounds*"]
marketOpen = False

def cashify(c):
    return "{:.2f}".format(round(c, 2))

def tryAgainMsg():
    return random.sample(tryAgainMsgs, 1)

def makePost(q, msg):
    #resp = fb.put_photo(image=open(img, 'rb'), message=msg)
    #postId = resp['id']
    
    imgUrl = getRandomImgUrl(q)
    fb.put_object(PAGE_ID, "photos", url=imgUrl, caption=msg)
    
def makeComment(parentId, msg):
    fb.put_object(parentId, "comments/comments", message=msg) 
    
def getComments(postId):
    comments = fb.get_connections(id=postId, connection_name='comments')
    
    allComments = []
    
    #### UNTESTED CODE AHEAD (possibly causing issues?)
    while True:
        try:
            for comment in comments['data']:
                commentId = comment['id']
                msg = comment['message']
                fromId = comment['from']['id']
                fromName = comment['from']['name']
                created = comment['created_time']
                if addComment(commentId, fromId, msg, created): # True if needs processing, False if already done
                    allComments.append((commentId, msg, fromId, created, fromName))
                else: log("Found already processed comments... From: " + fromName + " Msg: " + msg)
            comments = requests.get(comments['paging']['next']).json() # will throw exception when out of comments
        except KeyError:
            break
    ##### END OF UNTESTED CODE
    return allComments
    
def todaysPostOrNone():
    pagePosts = fb.get_connections(id=PAGE_ID,  connection_name='posts') # should get most recent posts, first page. No need to go farther
    
    for post in pagePosts['data']:
        created = datetime.strptime(post['created_time'], '%Y-%m-%dT%H:%M:%S+%f')
        #createdStr = str(created)#.split(' ')[0] # drop the time component (should probably use this to calulate when the market close is)****
        
        gmt = pytz.timezone('GMT')
        eastern = pytz.timezone('US/Eastern')
        
        createdLocalized = gmt.localize(created)
        createdEST = createdLocalized.astimezone(eastern)
        
        now = datetime.now()
        #nowStr = now.strftime('%Y-%m-%d')
        msg = ""
        if "message" in post:
            msg = post['message']
        #print('\n\n\nCreatStr: ' + str(createdEST.date()) + '\nNowStr: ' + str(now.date()))
        if createdEST.date() == now.date() and msg.startswith('The market is now open!'): # found a Market Open post from today
            log("Found todays post..")
            return post['id']
    log("Didn't find post for today, making one...")
    return None # couldn't find a Market Open post today
 
def getUserInfo(fbUserId, fromName):
    results = userInit(fbUserId, fromName)
    
    name = results[0]
    startedPlaying = results[1]
    cash = results[2]
    
    return "Name: " + name + "\nStarted playing: " + startedPlaying + "\nCash: $" + str(cashify(cash))

def userCash(userId, userName):
    userInfo = userInit(userId, userName)
    return userInfo[2]

def userBuy(userId, symbol, quantity, userName):
    usersCash = userCash(userId, userName)
    sharePrice = getPrice(symbol)
    if sharePrice is None or sharePrice == -1: #the latter is more likely
        return "Error while looking up stock price for " + symbol
    purchasePrice = sharePrice * int(quantity)
    purchase = takeUserCash(userId, purchasePrice)
    if purchase: # true if they had enough cash, false otherwise
        insertUserShares(userId, symbol, quantity)
        usersShares = userShares(userId, symbol)
        return "𝗦𝘁𝗼𝗰𝗸 𝗽𝘂𝗿𝗰𝗵𝗮𝘀𝗲𝗱!\n\n\n𝘙𝘦𝘤𝘦𝘪𝘱𝘵: You bought " + str(quantity) + "x " + str(symbol) + " @ $" + str(cashify(sharePrice)) + " = $" + str(cashify(purchasePrice)) + " total\n\n𝙔𝙤𝙪𝙧 𝙘𝙖𝙨𝙝 (before): $" + str(cashify(usersCash)) + "\n𝙔𝙤𝙪𝙧 𝙘𝙖𝙨𝙝 (after purchase): $" + str(cashify(userCash(userId, userName))) + "\n\nTotal stock in " + symbol + ": $" + str(cashify(int(usersShares) * sharePrice)) + " (" + str(usersShares) + " shares)"
    else:
        return "𝗡𝗼𝘁 𝗲𝗻𝗼𝘂𝗴𝗵 𝗺𝗼𝗻𝗲𝘆 (or error during checkout).\nTotal purchase price: $" + str(cashify(purchasePrice)) + "\nYour cash: $" + str(cashify(usersCash))
    
def userSell(userId, symbol, quantity, userName):
    usersCash = userCash(userId, userName)
    
    sharePrice = getPrice(symbol)
    shareVolume = userShares(userId, symbol)
    
    if int(quantity) > shareVolume: return "You don't hold that many shares!\nYou have " + str(shareVolume) + " shares." # trying to sell more shares than a user has
    
    salePrice = sharePrice * int(quantity)
    
    giveUserCash(userId, salePrice)
    deleteUserShares(userId, symbol, quantity) # returns False if it fails, probably verify this
    
    usersShares = userShares(userId, symbol)
    
    return "𝗦𝘁𝗼𝗰𝗸 𝘀𝗼𝗹𝗱!\n\n\n𝘙𝘦𝘤𝘦𝘪𝘱𝘵: You sold " + str(quantity) + "x " + symbol + " for $" + str(cashify(salePrice)) + "! ($" + str(cashify(sharePrice)) + " per share)\n\n𝙔𝙤𝙪𝙧 𝙘𝙖𝙨𝙝 (before): $" + str(cashify(usersCash)) + "\n𝙔𝙤𝙪𝙧 𝙘𝙖𝙨𝙝 (after sale): $" + str(cashify(userCash(userId, userName))) + "\n\n" + "Total stock in " + symbol + ": $" + str(cashify(int(usersShares) * sharePrice)) + " (" + str(usersShares) + " shares)"
    
def sanitizeUserInput(q): # sanitizes user input before being used in database queries. Very important to avoid SQL injection
    # stock symbols and quantities will never need to include characters like ,;'"()_=-~ etc. Only allow alpha numberic characters
    
    if not q.isalnum():
        forbiddenChars = [',', '\'', '"', ';', '-',  '_', '(', ')', '=', '*', '&', '^', '%', '$', '#', '@', '~,' '`', '>', '<', '?', '\\', ':', '[', ']', '{', '}', '|']
        
        for char in forbiddenChars:
            q = q.replace(char, '')
    
    return q


def processComments(): # called every few mins, calls getComments on todays Market Open Post and then does some SQL stuff
    # calculate todays Market Open Post, if none exists, create one
    todaysPost = todaysPostOrNone()
    if todaysPost is None:
        makePost('stock market', marketOpenTxt) # open market if not already open
        marketOpen = True
    else: # market has already opened, but may have since closed
        newComments = getComments(todaysPost) # returns (commentId, msg, fromId, created)
        if newComments is not None and len(newComments) > 0:
            log("New comments to process...")
            for comment in newComments:
                parentCommentId = comment[0]
                msg = comment[1]
                fromId = comment[2]
                created = comment[3]
                fromName = comment[4]
                
                log("Checking what to do with message from " + fromName + ", msg: " + msg)
                
                msg = sanitizeUserInput(msg.lower())
                if msg.startswith("!me") or msg.startswith("!status") or msg.startswith("/me") or msg.startswith("/status"):
                    #log("Making comment with status of user...")
                    makeComment(parentCommentId, getUserInfo(fromId, fromName))
                elif msg.startswith("!buy") or msg.startswith("/buy"):
                    params = msg.split(' ')
                    if len(params) == 3 and params[1].isdigit():
                        makeComment(parentCommentId, userBuy(fromId, params[2], params[1], fromName))
                    else:
                        makeComment(parentCommentId, tryAgainMsg())
                elif msg.startswith("!sell") or msg.startswith("/sell"):
                    params = msg.split(' ')
                    if len(params) == 3 and params[1].isdigit():
                        makeComment(parentCommentId, userSell(fromId, params[2], params[1], fromName))
                    else:
                        makeComment(parentCommentId, tryAgainMsg())
                    #makeComment(parentCommentId, "A financial hold has been placed on your account. Please contact customer support or try again in a few minutes.")
                elif msg.startswith("!price") or msg.startswith("/price"):
                    symbol = msg.split(' ')[1]
                    makeComment(parentCommentId, "The latest closing price in Yahoo Finance (and the effective price per share) for " + symbol + " is $" + cashify(getPrice(symbol)))
                else:
                    log("Unsupported command: " + msg)
                markCommentProcessed(parentCommentId, fromId, msg, created) # do this after processing, not before
                sleepRnd = random.randint(60*1, 60*3)
                log("Waiting " + str(sleepRnd/60) + " minutes for next action!")
                time.sleep(sleepRnd) # don't spam comments



#hreading.Timer(60.0 * random.randint(20, 40), processComments).start() # called every 20-40 minutes


###############################


##### PIL image processing stuff

#dailyLeaders = Image.open("DailyLeaders.png") # template for daily leaderboard
#fnt = ImageFont.truetype("MICROSS.ttf") # Microsoft Sans Serif
################################


while True:
    log("Looping...")
    processComments()
    waitTime = random.randint(2, 6)
    log("Waiting " + str(waitTime) + " minutes before checking for more comments")
    time.sleep(waitTime * 60) # don't spam comments
