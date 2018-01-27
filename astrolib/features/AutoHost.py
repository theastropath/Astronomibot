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

        self.hostChannel = ""
        self.hosting =  self.bot.api.isHosting(self.bot.channelId)

        if self.hosting:
            self.hostChannel = self.bot.api.getCurrentlyHostedChannel(self.bot.channelId) or ""



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

            if not self.bot.api.isStreamOnline(self.bot.channelId):
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
                    hostChannelId = self.bot.api.getChannelIdFromName(self.hostChannel)
                    if not self.bot.api.isStreamOnline(hostChannelId):
                        #Hosted channel is no longer online, stop hosting
                        self.stopHosting(sock)

                    #Make sure we are still hosting a channel
                    #If not, mark us as not hosting
                    if not self.bot.api.isHosting(self.bot.channelId):
                        self.stopHosting(sock)
                    else:
                        if self.hostTime > self.hostLength:
                            checkForNewHost = True
                        else:
                            self.hostTime += 1


                #Check for channels in host list that are online
                if not self.hosting or checkForNewHost:
                    for channel in self.hostList:
                        hostChannelId = self.bot.api.getChannelIdFromName(channel)
                        if self.bot.api.isStreamOnline(hostChannelId):
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
