import urllib
import json
import calendar
from datetime import timedelta
from astrolib.command import Command

class UpTime(Command):
    def __init__(self,bot,name):
        super(UpTime,self).__init__(bot,name)
        self.bot = bot
        self.lastKnownUptime=""

        if not self.bot.isCmdRegistered("!uptime"):
            self.bot.regCmd("!uptime",self)
        else:
            print("!uptime is already registered to ",self.bot.getCmdOwner("!uptime"))

    def getParams(self):
        params = []
        return params

    def setParam(self, param, val):
        pass

    def shouldRespond(self, msg, userLevel):
        if msg.messageType == 'PRIVMSG' and len(msg.msg)!=0:
            splitMsg = msg.msg.split()
            if splitMsg[0]=='!uptime':
                return True

        return False

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

    def getStreamLiveTime(self,channelName):
        req = urllib.request.Request("https://api.twitch.tv/kraken/streams/"+channelName)
        req.add_header('Client-ID',self.bot.clientId)
        try:
            response = urllib.request.urlopen(req)
            stream = response.read().decode()
            streamState = json.loads(stream)
            if streamState['stream']!=None:
                liveTime = streamState['stream']['created_at']
                startTime = time.strptime(liveTime, '%Y-%m-%dT%H:%M:%SZ')
                epochStartTime = calendar.timegm(startTime)
                curEpochTime = time.time()
                liveFor = curEpochTime-epochStartTime
                liveDelta = str(timedelta(seconds=int(liveFor)))
                self.lastKnownUptime = liveDelta
        except:
            pass

        return self.lastKnownUptime

    def getState(self):
        tables = []

        live = "No"
        if self.isStreamOnline(self.bot.channel[1:]):
            live = "Yes"

        state=[]
        state.append(("",""))
        state.append(("Channel Live?",live))
        if live == "Yes":
            state.append(("Live for",self.getStreamLiveTime(self.bot.channel[1:])))
        state.append(("",""))

        cmds = []
        cmds.append(("Command","Description"))
        cmds.append(("!uptime","Returns how long the channel has been live"))

        tables.append(state)
        tables.append(cmds)

        return tables

    def getDescription(self, full=False):
        if full:
            return "Users can get the amount of time that the channel has been live"
        else:
            return "Get the channels uptime!"


    def respond(self,msg,sock):
        response = ""
        channelName=self.bot.channel[1:]

        if not self.isStreamOnline(channelName):
            response = "Stream is not live"
        else:
            response = "Stream has been live for "+str(self.getStreamLiveTime(channelName))

        ircResponse = "PRIVMSG "+self.bot.channel+" :"+response+"\n"
        sock.sendall(ircResponse.encode('utf-8'))

        return response
