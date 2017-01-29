#!/usr/bin/env python3

from time import sleep
import time
from socket import *
from datetime import datetime
import os
import sys
import imp
import traceback
from collections import OrderedDict

from astrolib import EVERYONE, REGULAR, MOD, BROADCASTER, userLevelToStr
from astrolib.api import TwitchApi

twitchIrcServer = "irc.twitch.tv"
twitchIrcPort = 6667
credFile = "creds.txt"
channel = "#theastropath" #Channel name has to be all lowercase
logDir = "logs"
commandsDir = os.path.join("astrolib", "commands")
featuresDir = os.path.join("astrolib", "features")
configDir = "config"

nick=""
passw=""
clientId=""
clientSecret=""
accessToken=""

pollFreq=0.5

recvAmount=4096

running = True

#modList = [] #List of all moderators for the channel
#commands = []
#features = []


###############################################################################################################

class Bot:

    def importLogs(self):
        if not os.path.exists(configDir+os.sep+self.channel[1:]):
            os.makedirs(configDir+os.sep+self.channel[1:])

        try:
            with open(configDir+os.sep+self.channel[1:]+os.sep+self.logFile,encoding='utf-8') as f:
                for line in f:
                    logmsg = line.strip()
                    self.logs.append((logmsg.split("$$$")[0],logmsg.split("$$$")[1]))
        except FileNotFoundError:
            print ("Log file is not present")


    def __init__(self, channel, nick, pollFreq, api):
        self.modList = [] #List of all moderators for the channel
        self.commands = OrderedDict()
        self.features = OrderedDict()
        self.registeredCmds = []
        self.chatters = []
        self.logs = []
        self.logFile = "ActionLog.txt"
        self.channel = channel
        self._channelId = None
        self.regulars = []
        self.pollFreq = pollFreq
        self.name = nick
        self.api = api
        self.importLogs()

    # lazily loaded channel ID
    @property
    def channelId(self):
        if self._channelId is None:
            self._channelId = self.api.getChannelId()
        return self._channelId

    def getCommands(self):
        return self.commands.values()

    def getFeatures(self):
        return self.features.values()

    def getMods(self):
        return self.modList

    def getRegCmds(self):
        return self.registeredCmds

    def isCmdRegistered(self,cmd):
        for com in self.registeredCmds:
            if com[0] == cmd:
                return True
        return False

    def exportLogs(self):
        with open(configDir+os.sep+self.channel[1:]+os.sep+self.logFile,mode='w',encoding="utf-8") as f:
            for log in self.logs:
                f.write(log[0]+"$$$"+log[1]+"\n")



    def addLogMessage(self,msg):
        curTime = datetime.now().ctime()+" "+time.tzname[time.localtime().tm_isdst]
        self.logs.append((curTime,msg))
        if len(self.logs)>20:
            self.logs = self.logs[1:]
        self.exportLogs()


    def getLogs(self):
        return self.logs

    def regCmd(self,cmd,source):
        self.registeredCmds.append((cmd,source))

    def unregCmd(self,cmd):
        for com in self.registeredCmds:
            if com[0]==cmd:
                self.registeredCmds.remove(com)
                return
    def getCmdOwner(self,cmd):
        for com in self.registeredCmds:
            if com[0]==cmd:
                return str(cmd[1])
        return ""

    def getChatters(self):
        chat = []
        chatterList = self.chatters
        chatterList.sort()
        for chatter in chatterList:
            chat.append((chatter,userLevelToStr(self.getUserLevel(chatter))))
        return chat

    def checkCommandsAndFeatures(self):
        commandFiles = []
        for command in os.listdir(commandsDir):
            commandName, ext = os.path.splitext(command)
            if ".py" == ext and commandName not in self.commands:
                commandFiles.append(commandName)

        featureFiles = []
        for feature in os.listdir(featuresDir):
            featureName, ext = os.path.splitext(feature)
            if ".py" == ext and featureName not in self.features:
                featureFiles.append(featureName)

        for command in commandFiles:

            #Load file, and get the corresponding class in it, then instantiate it
            c = imp.load_source('astrolib.commands.'+command, os.path.join(commandsDir, command+".py"))
            try:
                cmd = getattr(c,command)
                self.commands[command] = cmd(self, command)
                print("Loaded command module '"+command+"'")
            except:
                traceback.print_exc()
                print("Couldn't load command module '"+command+"'")

        for feature in featureFiles:
            #Load file, and get the corresponding class in it, then instantiate it
            f = imp.load_source('astrolib.features.'+feature, os.path.join(featuresDir, feature+".py"))
            try:
                feat = getattr(f,feature)
                self.features[feature] = feat(self, feature)
                print("Loaded feature module '"+feature+"'")
            except:
                traceback.print_exc()
                print("Couldn't load feature module '"+feature+"'")


    def getUserLevel(self,userName):
        if userName==self.channel[1:]:
            #print(userName+" identified as broadcaster!")
            return BROADCASTER
        elif userName in self.modList:
            #print(userName+" identified as a mod!")
            return MOD
        elif userName in self.regulars:
            return REGULAR
        else:
            #print(userName+" identified as a scrub!")
            return EVERYONE


##############################################################################################
class IrcMessage:
    def __init__(self, message):
        msgstr = message.rstrip()
        breakdown = msgstr.split(None, 2)
        prefix = breakdown[0]
        messageType = breakdown[1]
        rest = breakdown[2] if len(breakdown) > 2 else ''
        #To determine what type of message it is, we can simply search
        #for the message type in the message.  However, we also need to
        #make sure it isn't just a user typing in a message type...
        #Therefore, for any type of message other than PRIVMSG, we need
        #to check to see if PRIVMSG is in there as well
        self.messageType = messageType
        self.sender = ''
        self.channel = ''
        self.msg = ''

        if messageType == 'PRIVMSG':
            breakdown = rest.split(None, 1)
            self.sender = prefix.split('!', 1)[0][1:]
            self.channel = breakdown[0]
            self.msg = breakdown[1][1:] if len(breakdown) > 1 else ''

        elif messageType == 'PING':
            self.msg = rest

        elif messageType == 'NOTICE':
            breakdown = rest.split(None, 1)
            self.sender = prefix[1:]
            self.channel = breakdown[0]
            self.msg = breakdown[1][1:] if len(breakdown) > 1 else ''

        elif messageType == 'JOIN':
            self.sender = prefix.split('!', 1)[0][1:]
            self.channel = rest
            self.msg = rest

        elif messageType == 'CAP':
            breakdown = rest.split(None, 2)
            self.sender = prefix[1:]
            # 'CAP * ACK'
            self.messageType = ' '.join((messageType, breakdown[0], breakdown[1]))
            self.msg = breakdown[2]

        elif messageType.isdecimal():
            # motd and such
            breakdown = rest.split(None, 1)
            self.receiver = breakdown[0]
            self.sender = prefix[1:]
            self.msg = breakdown[1][1:]

        if not self.msg:
            self.messageType = 'INVALID'



def handleNoticeMessage(msg):
    if "The moderators of this room are:" in msg.msg:
        #List of mods can be updated
        mods = msg.msg.split(": ")[1]
        for mod in mods.split(", "):
            bot.modList.append(mod.strip())
    else:
        print (msg.msg)

def logMessage(sender,msg):
    curTime = datetime.now()
    timestamp = curTime.strftime("%Y-%m-%d %H:%M:%S")
    logFile = curTime.strftime("%Y-%m-%d.txt")
    logMsg = timestamp+" - "+sender+": "+msg+"\n"
    channelLogDir = os.path.join(logDir, channel[1:])

    if not os.path.exists(channelLogDir):
        os.makedirs(channelLogDir)

    with open(os.path.join(channelLogDir, logFile), 'a', encoding='utf-8') as f:
        f.write(logMsg)

def connectToServer():
    print("Connecting to "+twitchIrcServer+":"+str(twitchIrcPort)+" as "+nick)

    sock = socket(AF_INET, SOCK_STREAM)

    connSuccess = False

    while not connSuccess:
        try:
            connSuccess = True
            sock.connect((twitchIrcServer,twitchIrcPort))
        except:
            connSuccess = False
            print ("Connection failed.  Retry...")
            sleep(10) #Wait 10 seconds, then try again

    sock.sendall(
        b"PASS "+passw.encode('ascii')+b"\n"+
        b"NICK "+nick.encode('ascii')+b"\n"+
        b"JOIN "+channel.encode('ascii')+b"\n"+
        b"CAP REQ :twitch.tv/commands\n"+
        b"CAP REQ :twitch.tv/membership\n")

    modUpdate = 1 #Start at 1 so that it will grab the mod list on the first pass

    sock.settimeout(pollFreq)

    return sock




if __name__ == "__main__":

    #Use channel name provided (IF one was provided)
    if len(sys.argv)>1:
        channel = sys.argv[1].lower()
        if channel[0]!='#':
            channel = '#'+channel
        print ("Connecting to provided channel '"+channel+"'")
    else:
        print ("Connecting to default channel '"+channel+"'")

    #Read credentials out of cred file
    try:
        with open(credFile) as f:
            nick = f.readline().strip('\n')
            passw = f.readline().strip('\n')
            clientId = f.readline().strip('\n')
            clientSecret = f.readline().strip('\n')
            accessToken = f.readline().strip('\n')
    except FileNotFoundError:
        print(credFile+" is missing!  Please create this file in your working directory.  First line should be the username for the bot, second line should be the oauth password for it!")
        exit(1)

    sock = connectToServer()
    api = TwitchApi(clientId, accessToken, clientSecret)
    bot = Bot(channel, nick, pollFreq, api)
    leftover = bytes()
    commandCheck=0

    while running:
        data = None

        if commandCheck<=0:
            #Get any commands or features
            bot.checkCommandsAndFeatures()
            commandCheck=600 #5 Minutes
        else:
            commandCheck-=1

        try:
            data = sock.recv(recvAmount)
            if leftover:
                data = leftover + data
        except BlockingIOError:
            pass
        except timeout:
            pass
        except ConnectionAbortedError:
            print ("Connection got aborted.  Reconnecting")
            sock = connectToServer()
        except ConnectionResetError:
            print ("Connection got forced closed.  Reconnecting")
            sock = connectToServer()
        except Exception as e:
            print ("Encountered exception '"+str(e.__class__.__name__)+"' while reading")
            sock = connectToServer()


        if data is not None:
            index = 0
            while True:
                next_index = data.find(b'\n', index)
                if next_index == -1:
                    # handle (unlikely) case where received data contains half a message
                    leftover = data[index:]
                    break
                message = data[index:next_index].decode(encoding='utf-8', errors='ignore')
                index = next_index + 1

                msg = IrcMessage(message)

                if msg.messageType == 'PRIVMSG':
                    logMessage(msg.sender,msg.msg)
                elif msg.messageType == '375':
                    # motd start
                    print("---------------------------")
                    print(msg.msg)
                elif msg.messageType == '372':
                    # motd
                    print(msg.msg)
                elif msg.messageType == '376':
                    # motd end
                    print(msg.msg)
                    print("---------------------------")


                for command in bot.getCommands():
                    if command.shouldRespond(msg,bot.getUserLevel(msg.sender)):
                        try:
                            response = command.respond(msg,sock)
                        except BrokenPipeError:
                            print ("Broken pipe while responding to command.  Reconnecting")
                            sock = connectToServer()
                        except Exception as e:
                            print ("Encountered exception '"+str(e.__class__.__name__)+"' while handling command "+str(command.name)+" handling message '"+str(msg.msg)+"'")
                            traceback.print_exc()
                            sock = connectToServer()

                        if len(response)>0:
                            logMessage(nick,response)

                if msg.messageType == 'NOTICE':
                    handleNoticeMessage(msg)


        for feature in bot.getFeatures():
            try:
                feature.handleFeature(sock)
            except BrokenPipeError:
                print ("Broken pipe while handling feature.  Reconnecting")
                sock = connectToServer()
            except Exception as e:
                print ("Encountered exception '"+str(e.__class__.__name__)+"' while handling feature "+str(feature.name))
                traceback.print_exc()
                sock = connectToServer()




    print ("DONE!")
    sock.close()
