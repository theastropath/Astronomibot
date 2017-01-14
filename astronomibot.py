#!/usr/bin/env python3

from time import sleep
import time
from socket import *
import json
from urllib.request import urlopen
from datetime import datetime
import os
import sys
import imp
import traceback

from astrolib import EVERYONE, REGULAR, MOD, BROADCASTER, userLevelToStr

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

replaceTerm="$REPLACE"
countTerm="$COUNT"
referenceCountTerm="$REF"

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


    def __init__(self, channel):
        self.modList = [] #List of all moderators for the channel
        self.commands = []
        self.features = []
        self.registeredCmds = []
        self.chatters = []
        self.logs = []
        self.logFile = "ActionLog.txt"
        self.channel = channel
        self.regulars = []
        self.pollFreq = pollFreq
        self.name = nick
        self.clientId = clientId
        self.clientSecret = clientSecret
        self.accessToken = accessToken
        self.importLogs()



    def getCommands(self):
        return self.commands

    def getFeatures(self):
        return self.features

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
                self.commands.append(cmd(self,command))
                print("Loaded command module '"+command+"'")
            except:
                print("Couldn't load command module '"+command+"'")

        for feature in featureFiles:
            #Load file, and get the corresponding class in it, then instantiate it
            f = imp.load_source('astrolib.features.'+feature, os.path.join(featuresDir, feature+".py"))
            try:
                feat = getattr(f,feature)
                self.features.append(feat(self,feature))
                print("Loaded feature module '"+feature+"'")
            except:
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
        breakdown = msgstr.split(' ', 2)
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
            breakdown = rest.split(' ', 1)
            self.sender = prefix.split('!', 1)[0][1:]
            self.channel = breakdown[0]
            self.msg = breakdown[1] if len(breakdown) > 1 else ''
        elif messageType == 'PING':
            self.msg = rest
        elif messageType == 'NOTICE':
            breakdown = rest.split(' ', 1)
            self.sender = prefix[1:]
            self.channel = breakdown[0]
            self.msg = breakdown[1] if len(breakdown) > 1 else ''

        if not self.msg:
            self.messageType = 'INVALID'




def getModList(channelName):
    #Web method, will keep as a backup, but not used for now
    response = urlopen('http://tmi.twitch.tv/group/user/'+channelName[1:]+'/chatters')
    chatters = response.read().decode()
    return (json.loads(chatters)["chatters"]["moderators"])

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
    channelLogDir = os.path.join(logDir, channels[1:])

    if not os.path.exists(channelLogDir):
        os.makedirs(channelLogDir)

    with open(os.path.join(channelLogDir, logFile), 'a', encoding='utf-8') as f:
        f.write(logMsg)

def connectToServer():
    print("Connecting to "+twitchIrcServer+":"+str(twitchIrcPort)+" as "+nick)

    sock = socket(AF_INET, SOCK_STREAM)

    connSuccess = False;

    while not connSuccess:
        try:
            connSuccess = True
            sock.connect((twitchIrcServer,twitchIrcPort))
        except:
            print ("Connection failed.  Retry...")
            connSuccess = False
            sleep(10) #Wait 10 seconds, then try again

    sock.sendall(b"PASS "+passw.encode('ascii')+b"\n")
    sock.sendall(b"NICK "+nick.encode('ascii')+b"\n")
    sock.sendall(b"JOIN "+channel.encode('ascii')+b"\n")
    sock.sendall(b"CAP REQ :twitch.tv/commands\n");
    sock.sendall(b"CAP REQ :twitch.tv/membership\n");


    sleep (1) #Wait for responses to roll in

    motd = sock.recv(recvAmount)
    print("---------------------------")
    print (str(motd))
    print("---------------------------")

    sock.setblocking(0)

    modUpdate = 1 #Start at 1 so that it will grab the mod list on the first pass

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
    bot = Bot(channel)

    while(running):
        message = ""

        #Get any commands or features
        bot.checkCommandsAndFeatures()

        try:
            message = sock.recv(recvAmount)
        except BlockingIOError:
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


        if message is not "":
            messages = message.decode().rstrip().split("\n")
            for m in messages:
                msg = IrcMessage(m)

                if msg.messageType == 'PRIVMSG':
                    logMessage(msg.sender,msg.msg)

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




        sleep(pollFreq)
    print ("DONE!")
    sock.close()
