import os
from astrolib.feature import Feature
import time
import json
configDir = "config"

class AutoHost(Feature):
    def initConfig(self):
        if "AutoHost" not in self.bot.config:
            self.bot.config["AutoHost"] = {}

        if "hostcheckfreq" in self.bot.config["AutoHost"]:
            self.hostCheckFrequency = int(self.bot.config["AutoHost"]["hostcheckfreq"]) * 2
        else:
            self.bot.config["AutoHost"]["hostcheckfreq"] = str(int(self.hostCheckFrequency/2))
        
        if "hostlength" in self.bot.config["AutoHost"]:
            self.hostLength = int(self.bot.config["AutoHost"]["hostlength"])
        else:
            self.bot.config["AutoHost"]["hostlength"] = str(int(self.hostLength))

        if "gameblocklist" in self.bot.config["AutoHost"]:
            self.gameBlockList = json.loads(self.bot.config["AutoHost"]["gameblocklist"])
        else:
            self.bot.config["AutoHost"]["gameblocklist"] = json.dumps(self.gameBlockList)
        
        
    def __init__(self,bot,name):
        super(AutoHost,self).__init__(bot,name)

        self.hostCheckFrequency = 240 #In units based on the pollFreq (in astronomibot.py)
        self.hostLength = 15 #In units based on the hostCheckFrequency!
        self.gameBlockList = []

        self.initConfig()

        self.hostUpdate = 1
        self.hostTime = 0
        self.offlineTime = 0
        self.hostList = []
        self.hostListFile = "AutoHostList.txt"

        self.gameBlockList = []

        self.hostChannel = ""
        self.hosting =  (self.bot.hostedChannel!=None)
        self.botUnhost=False

        self.bot.subToNotices(self.handleNotice)
        self.coolOff = 0

        if self.hosting:
            self.hostChannel = self.bot.hostedChannel

    def handleNotice(self,noticeMsg):
        if noticeMsg.tags:
            if noticeMsg.tags['msg-id']=='host_off':
                self.hostTime = 0
                self.hostChannel=""
                self.hosting = False
                if not self.botUnhost:
                    self.coolOff = 1200 #Apply a cool-off, just in case it was manually unhosted
                else:
                    self.botUnhost = False
                self.bot.addLogMessage("AutoHost: No longer hosting")
                return True
            elif noticeMsg.tags['msg-id']=='host_on':
                hostChannel = noticeMsg.msg.split()[-1].strip(".").strip().lower()
                self.hostTime = 0
                self.hostChannel=hostChannel
                self.hosting = True
                self.bot.addLogMessage("AutoHost: Now hosting "+hostChannel)
                return True
            elif noticeMsg.tags['msg-id']=='host_target_went_offline':
                self.hostTime = 0
                self.hostChannel=""
                self.hosting = False
                self.coolOff = 600 #Apply a cool-off
                self.bot.addLogMessage("AutoHost: No longer hosting, hosted channel went offline")
                return True

        return False

    def outputHostList(self):
        hostListDir = os.path.join(configDir, self.bot.channel[1:])
        os.makedirs(hostListDir, exist_ok=True)
        hostListPath = os.path.join(hostListDir, self.hostListFile)

        with open(hostListPath,mode='w',encoding="utf-8") as f:
            for channel in self.hostList:
                f.write(channel.lower()+"\r\n")

    def readHostList(self):
        #Load regulars
        hostListPath = os.path.join(configDir, self.bot.channel[1:], self.hostListFile)

        try:
            with open(hostListPath,encoding='utf-8') as f:
                self.hostList = [line.strip() for line in f]
                self.hostList = list(filter(None,self.hostList))
        except FileNotFoundError:
            print("Host List file is not present: %s" % hostListPath)


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

    def sendMessage(self,message,sock):
        msg = "PRIVMSG %s :%s\n" % (self.bot.channel, message)
        sock.sendall(msg.encode('utf-8'))

    def startHosting(self,hostChannel,sock):
        self.hostTime = 0
        self.hostChannel=hostChannel
        self.hosting = True
        self.sendMessage("/host "+hostChannel,sock)

    def stopHosting(self,sock):
        self.hostTime = 0
        self.hostChannel=""
        self.hosting = False
        self.botUnhost=True
        self.sendMessage("/unhost",sock)



    def handleFeature(self,sock):
        checkForNewHost = False
        if self.coolOff:
            self.coolOff= self.coolOff - 1
            return
        
        #Check to see if we need to look for hosting opportunities
        self.hostUpdate = self.hostUpdate - 1
        if self.hostUpdate == 0:
            self.readHostList()
            
            self.hostUpdate = self.hostCheckFrequency

            if not self.bot.streamOnline:
                #Stream must be offline for several checks in a row
                #(To prevent an occasional lookup failure from hosting during a stream)
                self.offlineTime += 1
                if self.offlineTime <= 3:
                    #print("Stream offline "+str(self.offlineTime))
                    return
                else:
                    self.offlineTime = 4 #Prevent it from rolling over during long periods of offline



                #Stream is offline.
                if self.hosting:
                    #Check if hosted channel is still online, and stop hosting if not
                    #hostChannelId = self.bot.api.getChannelIdFromName(self.hostChannel)
                    if not self.bot.api.isStreamOnlineHelix(self.hostChannel):
                        #Hosted channel is no longer online, stop hosting
                        self.stopHosting(sock)
                        

                    #Make sure we are still hosting a channel
                    #If not, mark us as not hosting
                if self.hosting:
                    if self.bot.hostedChannel == None:
                        self.stopHosting(sock)
                    else:
                        if self.hostTime > self.hostLength:
                            checkForNewHost = True
                        else:
                            self.hostTime += 1

                #Make sure we aren't hosting someone who is playing a game we have blocked
                if self.hosting:
                    gamename = self.bot.api.getGameByNameHelix(self.bot.hostedChannel)
                    if gamename in self.gameBlockList:
                        print(self.bot.hostedChannel+" is now playing a blocked game ("+gamename+")")
                        self.stopHosting(sock)

                #Check for channels in host list that are online
                if not self.hosting or checkForNewHost:
                    streamList = self.bot.api.getOnlineStreamsAndGamesHelix(self.hostList)

                    onlineList = []
                    for stream in streamList:
                        channel = stream[0]
                        gamename = stream[1]
                        #print(channel+" is streaming "+gamename)
                        if gamename not in self.gameBlockList:
                            onlineList.append(channel)
                        else:
                            print(channel+" is streaming blocked game "+gamename)

                    if len(onlineList)>0:
                        #print(str(onlineList))
                        for channel in self.hostList:
                            #hostChannelId = self.bot.api.getChannelIdFromName(channel)
                            if channel.lower() in onlineList:
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
                #print("Stream Online...")
                if self.hosting:
                    #send unhost message
                    self.stopHosting(sock)
                self.hosting = False
                self.offlineTime = 0
                self.hostUpdate = 3 * self.hostCheckFrequency
