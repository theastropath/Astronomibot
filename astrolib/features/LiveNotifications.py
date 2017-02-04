import os
from astrolib.feature import Feature
import calendar
import time
import tweepy

configDir = "config"
twitterCredFile = "twittercreds.txt"

class LiveNotifications(Feature):

    def __init__(self,bot,name):
        super(LiveNotifications,self).__init__(bot,name)

        self.liveCheckFrequency = 120 #In units based on the pollFreq (in astronomibot.py)
        self.liveNotificationCoolOff = 60 * 60 * 2 #Cool off period is 1 hour by default

        self.liveCheck = 1

        self.live = False

        self.tweet=False
        self.twitterApi=None

        self.discord=False
        self.discordApi=None

        try:
            with open(twitterCredFile) as f:
                self.consumerkey = f.readline().strip('\n')
                self.consumersecret = f.readline().strip('\n')
                self.accesstoken = f.readline().strip('\n')
                self.accesstokensecret = f.readline().strip('\n')

                self.tweet=True
        except FileNotFoundError:
            pass #No FTP cred file found.  Just won't try to upload.

        if self.tweet:
            auth = tweepy.OAuthHandler(self.consumerkey,self.consumersecret)
            auth.set_access_token(self.accesstoken,self.accesstokensecret)
            
            self.twitterApi = tweepy.API(auth)

        #Check to see if channel is live
        #If live, check to see how long channel has been live
        #If live for less than liveCheckFrequency, stay offline
        #Else, mark channel as live so that no notification goes out
        startTime = self.bot.api.getStreamLiveTime(self.bot.channelId)
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

        if len(tweet)>140:
            diff = len(tweet)-140
            tweet = msg[:-diff-3]+"...\n"+url

        self.twitterApi.update_status(tweet)

    def sendDiscordMsg(self,msg, url):
        print("Discording '"+msg+"'")

    def sendNotifications(self):
        notifyMsg = self.bot.api.getTitle(self.bot._channelId)
        notifyUrl = self.bot.api.getChannelUrl(self.bot._channelId)
        
        if self.tweet:
            self.sendTweet(notifyMsg, notifyUrl)

        if self.discord:
            self.sendDiscordMsg(notifyMsg, notifyUrl)

    def handleFeature(self,sock):
        #Check to see if we need to look for hosting opportunities
        self.liveCheck = self.liveCheck - 1
        if self.liveCheck == 0:

            self.liveCheck = self.liveCheckFrequency

            online =  self.bot.api.isStreamOnline(self.bot.channelId)
            if (online and not self.live):
                self.bot.addLogMessage("Stream has gone live")
                self.live = True
                self.sendNotifications()
                self.liveCheck = self.liveNotificationCoolOff
            elif (not online and self.live):
                self.bot.addLogMessage("Stream has gone offline")
                self.live = False
