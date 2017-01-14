from astrolib.command import Command
from astrolib import MOD

class ScheduledMsg():

    def __init__(self,bot,cmd,freq,numBetween):
        #Frequency in terms of ticks
        self.cmd = cmd
        self.freq = freq
        self.numBetween = numBetween
        self.started = False
        self.bot = bot

        self.customCmds = self.bot.commands[self.bot.commands.index("CustomCmds")]
        self.tick=0
        self.numMsgs=0

    def runMsg(self):
        response = "Running scheduled message "+self.cmd
        if self.cmd in self.customCmds.customCmds.keys():
            response=self.customCmds.customCmds[self.cmd].handleVariables("")
        else:
            self.stop()
            response="Command "+self.cmd+" has not been configured"
        #   command.getResponse("")
        return response

    def start(self):
        self.started=True

    def stop(self):
        self.started=False

    def countMsg(self):
        self.numMsgs+=1

    def __eq__(self,key):
        return key == self.cmd

    def tickMsg(self):
        response = ""

        if not self.started:
            return response

        self.tick+=1
        if self.tick>=self.freq:
            if (self.numMsgs>=self.numBetween):
                response = self.runMsg()
                self.tick=0
                self.numMsgs=0

        return response



class ScheduledMsgCmd(Command):

    args = ["create","start","stop","delete"]

    INVALIDVALUE=-1


    def __init__(self,bot,name):
        super(ScheduledMsgCmd,self).__init__(bot,name)
        self.maxFreq = 120
        self.maxMsgBetween = 100

        self.schedMsgs = {}
        if not self.bot.isCmdRegistered("!schedulemsg"):
            self.bot.regCmd("!schedulemsg",self)
        else:
            print("!schedulemsg is already registered to ",self.bot.getCmdOwner("!schedulemsg"))


    def getParams(self):
        params = []
        return params

    def setParam(self, param, val):
        pass

    def createSched(self,cmd,freq,msgBetween):
        response = "Scheduling command '"+cmd+"' to run every "+str(freq)+" minutes, with at least "+str(msgBetween)+" messages between"

        #Frequency being passed in is specified in minutes,
        #whereas the frequency I want to keep track of should be in ticks
        tickFreq = freq * 60 * 2

        self.schedMsgs[cmd]=ScheduledMsg(self.bot,cmd,tickFreq,msgBetween)

        return response

    def startSched(self,cmd):
        response = "Starting command '"+cmd+"'"
        self.schedMsgs[cmd].start()
        return response

    def stopSched(self,cmd):
        response = "Stopping command '"+cmd+"'"
        self.schedMsgs[cmd].stop()
        return response

    def deleteSched(self,cmd):
        response = "Deleting command '"+cmd+"'"
        del self.schedMsgs[cmd]
        return response

    def shouldRespond(self, msg, userLevel):

        #Increment number of messages between scheduled msgs for every message NOT from twitchnotify
        if msg.messageType == 'PRIVMSG' and len(msg.msg)!=0 and msg.sender!='twitchnotify':
            for cmd in self.schedMsgs:
                self.schedMsgs[cmd].countMsg()

        if msg.messageType == 'PRIVMSG' and len(msg.msg)!=0 and userLevel>=MOD:
            fullmsg = msg.msg.split()
            if len(fullmsg)>=3 and fullmsg[0].lower()=="!schedulemsg":
                if fullmsg[1][0]=='!':
                    if fullmsg[2].lower() in self.args:
                        if fullmsg[2].lower()!="create":
                            if len(fullmsg)==3:
                                return True
                        else:
                            #Create requires a few more parameters:
                            #Requires message frequency in minutes and optionally messages between
                            if len(fullmsg)==4 or len(fullmsg)==5:
                                return True

        return False

    def respond(self,msg,sock):
        fullmsg = msg.msg.split()
        scheduledCmd = fullmsg[1].lower()
        arg = fullmsg[2].lower()
        frequency = 0
        msgBetween = 0

        response = ""

        if len(fullmsg)>3 and arg=="create":
            try:
                frequency = int(fullmsg[3])
            except ValueError:
                frequency = self.INVALIDVALUE

            if frequency > self.maxFreq:
                frequency = self.INVALIDVALUE

            if len(fullmsg)>4:
                try:
                    msgBetween = int(fullmsg[4])
                except ValueError:
                    msgBetween = self.INVALIDVALUE

                if msgBetween > self.maxMsgBetween:
                    msgBetween = self.INVALIDVALUE

        if arg == "create":
            validConfig=(frequency>0 and msgBetween>=0)

            #Check to see if command has already been scheduled.
            if scheduledCmd in self.schedMsgs.keys():
                response = "Command has already been scheduled"
            else:
                if validConfig:
                    response = self.createSched(scheduledCmd,frequency,msgBetween)
                else:
                    response = "Invalid parameters for creation"
        elif arg == "start" or arg == "stop" or arg == "delete":
                #Ensure the scheduled command has already been created
                if scheduledCmd not in self.schedMsgs.keys():
                    response = "Command has not yet been scheduled"
                else:
                    #If already created:
                    if arg=="start":
                        response=self.startSched(scheduledCmd)
                    elif arg=="stop":
                        response=self.stopSched(scheduledCmd)
                    elif arg=="delete":
                        response=self.deleteSched(scheduledCmd)

        ircResponse = "PRIVMSG "+self.bot.channel+" : "+response+"\n"
        sock.sendall(ircResponse.encode('utf-8'))

        return response
