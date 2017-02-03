import calendar
import time
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

    def getStreamLiveTime(self, channelName):
        startTime = self.bot.api.getStreamLiveTime(channelName)
        if startTime is not None:
            epochStartTime = calendar.timegm(startTime)
            curEpochTime = time.time()
            liveFor = curEpochTime - epochStartTime
            liveDelta = str(timedelta(seconds=int(liveFor)))
            self.lastKnownUptime = liveDelta

        return self.lastKnownUptime

    def getState(self):
        tables = []

        live = "No"
        if self.bot.api.isStreamOnline(self.bot.channelId):
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

        if not self.bot.api.isStreamOnline(self.bot.channelId):
            response = "Stream is not live"
        else:
            response = "Stream has been live for %s" % self.getStreamLiveTime(channelName)

        ircResponse = "PRIVMSG %s :%s\n" % (self.bot.channel, response)
        sock.sendall(ircResponse.encode('utf-8'))

        return response
