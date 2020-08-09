import os
from astrolib.feature import Feature
import calendar
import time
import tweepy
import json
import threading

from requests import Session

configDir = "config"
twitterCredFile = "twittercreds.txt"
discordCredFile = "discordcreds.txt"

class LiveNotifications(Feature):

    def __init__(self,bot,name):
        super(LiveNotifications,self).__init__(bot,name)

        self.liveCheckFrequency = 10 #In units based on the pollFreq (in astronomibot.py)
        self.liveNotificationCoolOff = 60 * 60 * 2 #Cool off period is 1 hour by default

        self.liveCheck = 1

        self.live = False

        self.tweet=False
        self.twitterApi=None

        self.discord=False
        self.discordApi=None

        self.twitConsumerkey =       self.bot.config["Twitter"]["consumerkey"]
        self.twitConsumersecret =    self.bot.config["Twitter"]["consumersecret"] 
        self.twitAccesstoken =       self.bot.config["Twitter"]["accesstoken"]
        self.twitAccesstokensecret = self.bot.config["Twitter"]["accesstokensecret"]

        if self.twitConsumerkey!="":
            self.tweet = True

        self.discordClientId =     self.bot.config["Discord"]["clientid"]
        self.discordClientSecret = self.bot.config["Discord"]["clientsecret"]
        self.discordUserName =     self.bot.config["Discord"]["username"]
        self.discordUserId =       self.bot.config["Discord"]["userid"]
        self.discordAccessToken =  self.bot.config["Discord"]["accesstoken"]
        self.discordChannelId =    self.bot.config["Discord"]["channelid"]

        if self.discordClientId !="":
            self.discord = True
            
        if self.tweet:
            auth = tweepy.OAuthHandler(self.twitConsumerkey,self.twitConsumersecret)
            auth.set_access_token(self.twitAccesstoken,self.twitAccesstokensecret)
            
            self.twitterApi = tweepy.API(auth)

        #Check to see if channel is live
        #If live, check to see how long channel has been live
        #If live for less than liveCheckFrequency, stay offline
        #Else, mark channel as live so that no notification goes out
        startTime = self.bot.api.getStreamLiveTimeHelix(self.bot.channelName)
        if startTime is not None:
            epochStartTime = calendar.timegm(startTime)
            curEpochTime = time.time()
            liveFor = curEpochTime - epochStartTime
            if liveFor > self.liveCheckFrequency:
                self.liveCheck = self.liveNotificationCoolOff
                self.live = True


    def getParams(self):
        params = []
        return params

    def sendMessage(self,message,sock):
        msg = "PRIVMSG %s :%s\n" % (self.bot.channel, message)
        sock.sendall(msg.encode('utf-8'))

    def sendTweet(self,msg, url):
        #print("Tweeting '"+msg+"\n"+url+"'")
        tweet = msg+"\n"+url

        if len(tweet)>280:
            diff = len(tweet)-280
            tweet = msg[:-diff-3]+"...\n"+url
        try:
            self.twitterApi.update_status(tweet)
        except Exception as e:
            print("Encountered an issue when attempting to tweet: "+str(e))

    def sendDiscordMsg(self,msg, url):
        notifyMsg = "Now live!\n"+msg+"\n"+url
        content = {"content": notifyMsg}
        content = json.dumps(content).encode('utf-8')
        discordMsgApi = "https://discord.com/api/channels/"+self.discordChannelId+"/messages"
        session=Session()
        response = session.request('POST', discordMsgApi, data=content,headers={
            'Authorization': 'Bot '+self.discordAccessToken,
            'User-Agent': 'Astronomibot (astronomibot.xyz, v1)',
            'Content-Type': 'application/json'
        })


    def sendNotifications(self):
        notifyMsg = self.bot.api.getTitleByNameHelix(self.bot.channelName)
        notifyUrl = self.bot.api.getChannelUrlFromNameHelix(self.bot.channelName)
        
        if self.tweet:
            self.sendTweet(notifyMsg, notifyUrl)

        if self.discord:
            self.sendDiscordMsg(notifyMsg, notifyUrl)

    def handleFeature(self,sock):
        #Check to see if we need to look for hosting opportunities
        self.liveCheck = self.liveCheck - 1
        if self.liveCheck == 0:

            self.liveCheck = self.liveCheckFrequency

            if (self.bot.streamOnline and not self.live):
                self.bot.addLogMessage("Stream has gone live")
                self.live = True

                self.notifThread = threading.Thread(target=self.sendNotifications)
                self.notifThread.start()

                self.liveCheck = self.liveNotificationCoolOff
            elif (not self.bot.streamOnline and self.live):
                self.bot.addLogMessage("Stream has gone offline")
                self.live = False
