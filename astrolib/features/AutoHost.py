import urllib
import json
import os
from astrolib.feature import Feature

configDir = "config"

class AutoHost(Feature):

    def __init__(self,bot,name):
        super(AutoHost,self).__init__(bot,name)

        self.hostCheckFrequency = 240 #In units based on the pollFreq (in astronomibot.py)
        self.hostLength = 15 #In units based on the hostCheckFrequency!

        self.hostUpdate = 1
        self.hostTime = 0
        self.offlineTime = 0
        self.hostList = []
        self.hostListFile = "AutoHostList.txt"

        self.channelId=0
        self.hostChannel = ""
        self.hosting =  self.currentlyHosting(self.bot.channel[1:])

        if self.hosting:
            self.hostChannel = self.currentHostedChannel(self.bot.channel[1:])



    def outputHostList(self):
            with open(configDir+os.sep+self.bot.channel[1:]+os.sep+self.hostListFile,mode='w',encoding="utf-8") as f:
                for channel in self.hostList:
                    f.write(channel.lower()+"\n")

    def readHostList(self):
        #Load regulars
        if not os.path.exists(configDir+os.sep+self.bot.channel[1:]):
            os.makedirs(configDir+os.sep+self.bot.channel[1:])

        try:
            with open(configDir+os.sep+self.bot.channel[1:]+os.sep+self.hostListFile,encoding='utf-8') as f:
                self.hostList=[]
                for line in f:
                    channel = line.strip()
                    self.hostList.append(channel)
        except FileNotFoundError:
            print ("Host List file is not present")


    def getParams(self):
        params = []
        params.append({'title':'HostCheckFrequency','desc':'How frequently we check for other live channels to host (seconds)','val':self.hostCheckFrequency/2})
        params.append({'title':'HostLength','desc':'How long we will host a channel before looking for a higher priority channel to host (seconds)','val':(self.hostLength * self.hostCheckFrequency/2)})

        return params

    def setParam(self, param, val):
        if param == 'HostCheckFrequency':
            self.hostCheckFrequency = float(val) * 2
        elif param == 'HostLength':
            self.hostLength = float(val) / self.hostCheckFrequency


    def isStreamOnline(self,channelName):
        req = urllib.request.Request("https://api.twitch.tv/kraken/streams/"+channelName)
        req.add_header('Client-ID',self.bot.clientId)
        try:
            response = urllib.request.urlopen(req)
            stream = response.read().decode()
            streamState = json.loads(stream)
            if streamState['stream']!=None:
                return True
        except:
            pass

        return False

    def currentlyHosting(self,channelName):
        if self.channelId==0:
            #Gotta get the channel ID first...
            req = urllib.request.Request("https://api.twitch.tv/kraken/channels/"+channelName)
            req.add_header('Client-ID',self.bot.clientId)
            try:
                response = urllib.request.urlopen(req)
                channels = response.read().decode()
                channelsVal = json.loads(channels)
                chanId = channelsVal['_id']
                self.channelId = chanId
            except:
                pass

        if self.channelId!=0:
            #Check to see if we are hosting another channel
            req = urllib.request.Request("https://tmi.twitch.tv/hosts?include_logins=1&host="+str(self.channelId))
            try:
                response = urllib.request.urlopen(req)
                hosts = response.read().decode()
                hostsList = json.loads(hosts)
                if 'target_login' in hostsList['hosts'][0].keys():
                    return True

            except:
                pass

        return False

    def currentHostedChannel(self,channelName):
        if self.channelId==0:
            #Gotta get the channel ID first...
            req = urllib.request.Request("https://api.twitch.tv/kraken/channels/"+channelName)
            req.add_header('Client-ID',self.bot.clientId)
            try:
                response = urllib.request.urlopen(req)
                channels = response.read().decode()
                channelsVal = json.loads(channels)
                chanId = channelsVal['_id']
                self.channelId = chanId
            except:
                pass

        if self.channelId!=0:
            #Check to see if we are hosting another channel
            req = urllib.request.Request("https://tmi.twitch.tv/hosts?include_logins=1&host="+str(self.channelId))
            try:
                response = urllib.request.urlopen(req)
                hosts = response.read().decode()
                hostsList = json.loads(hosts)
                if 'target_login' in hostsList['hosts'][0].keys():
                    return hostsList['hosts'][0]['target_login']

            except:
                pass

        return ""

    def sendMessage(self,message,sock):
        msg = "PRIVMSG "+self.bot.channel+" :"+message+"\n"
        sock.sendall(msg.encode('utf-8'))

    def startHosting(self,hostChannel,sock):
        self.hostTime = 0
        self.hostChannel=hostChannel
        self.hosting = True
        self.bot.addLogMessage("AutoHost: Now hosting "+hostChannel)
        self.sendMessage("/host "+hostChannel,sock)

    def stopHosting(self,sock):
        self.hostTime = 0
        self.hostChannel=""
        self.hosting = False
        self.bot.addLogMessage("AutoHost: No longer hosting")
        self.sendMessage("/unhost",sock)



    def handleFeature(self,sock):
        checkForNewHost = False
        #Check to see if we need to look for hosting opportunities
        self.hostUpdate = self.hostUpdate - 1
        if self.hostUpdate == 0:
            self.readHostList()

            self.hostUpdate = self.hostCheckFrequency

            if not self.isStreamOnline(self.bot.channel[1:]):
                #Stream must be offline for several checks in a row
                #(To prevent an occasional lookup failure from hosting during a stream)
                self.offlineTime += 1

                if self.offlineTime < 3:
                    return
                else:
                    self.offlineTime = 3 #Prevent it from rolling over during long periods of offline

                #Stream is offline.
                if self.hosting:
                    #Make sure we are still hosting a channel
                    #If not, mark us as not hosting
                    if not self.currentlyHosting(self.bot.channel[1:]):
                        self.stopHosting(sock)
                    else:
                        if self.hostTime > self.hostLength:
                            checkForNewHost = True
                        else:
                            self.hostTime += 1


                #Check for channels in host list that are online
                if not self.hosting or checkForNewHost:
                    for channel in self.hostList:
                        if self.isStreamOnline(channel):
                            if not checkForNewHost: #IN the normal case, just host the highest priority stream
                                self.startHosting(channel,sock)
                                return
                            else: #If we're past the host time, we'll check to see if there is a different stream to host
                                if channel != self.hostChannel:
                                    print ("We were hosting "+self.hostChannel+" now hosting "+channel)
                                    self.startHosting(channel,sock)
                                    return
                                elif channel == self.hostChannel:
                                    #We'll stick with the current stream if it is higher priority
                                    return

            else:
                if self.hosting:
                    #send unhost message
                    self.stopHosting(sock)
                self.hosting = False
                self.offlineTime = 0
