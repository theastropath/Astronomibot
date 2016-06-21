from time import sleep
from socket import *
import json
from urllib.request import urlopen
from datetime import datetime
import os
import sys
import imp

twitchIrcServer = "irc.twitch.tv"
twitchIrcPort = 6667
credFile = "creds.txt"
channel = "#theastropath" #Channel name has to be all lowercase
logDir = "logs"
commandsDir = "commands"
featuresDir = "features"
configDir = "config"

nick=""
passw=""

pollFreq=0.5

recvAmount=4096

EVERYONE=1
REGULAR = 2
MOD=3
BROADCASTER=4

replaceTerm="$REPLACE"

running = True

#modList = [] #List of all moderators for the channel
#commands = []
#features = []

#############################################################################################################
# These two classes define the API for interacting with "commands" and "features"
# Implementations of these classes must be made in an individual .py file in the command
# or feature folder, and the implemented class must have the same name as the file
#############################################################################################################

class Command:
    name = ""
    
    #This function will take a msg and respond if this "command" should respond (True or False)
    def shouldRespond(self, msg, userLevel):
        raise NotImplementedError()

    #This function will actually respond to the message
    def respond(self,msg,sock):
        raise NotImplementedError()

    def getParams(self):
        params = []
        return params

    def setParam(self, param, val):
        pass

    def getState(Self):
        return None

    def getDescription(self,full=False):
        return "A generic undescribed Command"
    
    #Equals is used for checking if the name is in the command list
    def __eq__(self,key):
        return key == self.name

    def __init__(self,bot,name):
        self.name = name
        self.bot = bot

class Feature:
    name = ""

    #This function will go off and do whatever this feature is supposed to do
    def handleFeature(self,sock):
        raise NotImplementedError()
    
    def getParams(self):
        params = []
        return params

    def setParam(self, param, val):
        pass

    def getState(self):
        return None

    def getDescription(self,full=False):
        return "A generic undescribed Feature"
    
    #Equals is used for checking if the name is in the feature list
    def __eq__(self,key):
        return key == self.name
    
    def __init__(self,bot,name):
        self.name = name
        self.bot = bot


###############################################################################################################    

class Bot:
    modList = [] #List of all moderators for the channel
    commands = []
    features = []
    registeredCmds = []
    chatters = []
    regulars = []
    
    def __init__(self,channel):
        self.channel = channel
        self.regulars = []
        self.pollFreq = pollFreq
        self.name = nick



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
            commandName = command[:-3]
            if ".py" in command[-3:] and commandName not in self.commands:
                commandFiles.append(commandName)

        featureFiles = []  
        for feature in os.listdir(featuresDir):
            featureName = feature[:-3]
            if ".py" in feature[-3:] and featureName not in self.features:
                featureFiles.append(featureName)

        for command in commandFiles:

            #Load file, and get the corresponding class in it, then instantiate it
            c = imp.load_source('Command',commandsDir+os.sep+command+".py")
            cmd = getattr(c,command)
            
            self.commands.append(cmd(self,command))
            print("Loaded command module '"+command+"'")
            
        for feature in featureFiles:
            #Load file, and get the corresponding class in it, then instantiate it
            f = imp.load_source('Feature',featuresDir+os.sep+feature+".py")
            feat = getattr(f,feature)
            
            self.features.append(feat(self,feature))
            print("Loaded feature module '"+feature+"'")
                
    def getUserLevel(self,userName):
        if userName==channel[1:]:
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
    sender = ""
    messageType = ""
    channel = ""
    msg = ""

    def __init__(self, message):
        msgstr=message.rstrip()
        breakdown = msgstr.split()
        #To determine what type of message it is, we can simply search
        #for the message type in the message.  However, we also need to
        #make sure it isn't just a user typing in a message type...
        #Therefore, for any type of message other than PRIVMSG, we need
        #to check to see if PRIVMSG is in there as well
        if ("PRIVMSG" in msgstr):
            self.messageType = breakdown[1]
            self.sender = breakdown[0].split("!")[0][1:]
            self.channel = breakdown[2]
            self.msg = " ".join(breakdown[3:])[1:]
        elif ("PING" in msgstr and "PRIVMSG" not in msgstr):
            self.messageType = "PING"
            self.msg = breakdown[1]
        elif ("NOTICE" in msgstr and "PRIVMSG" not in msgstr):
            self.messageType = "NOTICE"
            self.sender = breakdown[0][1:]
            self.channel = breakdown[2]
            self.msg = " ".join(breakdown[3:])[1:]        
        else:
            #Who cares?
            self.messageType = "MEH"

        if (len(self.msg)==0):
            self.messageType = "INVALID"


def userLevelToStr(userLevel):
    if userLevel == EVERYONE:
        return "Everyone"
    elif userLevel == REGULAR:
        return "Regular Viewer"
    elif userLevel == MOD:
        return "Moderator"
    elif userLevel == BROADCASTER:
        return "Broadcaster"
    else:
        return "???"



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
    logFile = curTime.strftime("%Y-%m-%d")+".txt"
    logMsg = (timestamp+" - "+sender+": "+msg+"\n")

    if not os.path.exists(logDir+os.sep+channel[1:]):
        os.makedirs(logDir+os.sep+channel[1:])

    f = open(logDir+os.sep+channel[1:]+os.sep+logFile,'a',encoding='utf-8')
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
        f = open(credFile)
        nick = f.readline().strip('\n')
        passw = f.readline().strip('\n')
        f.close()
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

        if message is not "":
            messages = message.decode().rstrip().split("\n")
            for m in messages:
                msg = IrcMessage(m)
                
                if msg.messageType == 'PRIVMSG':
                    logMessage(msg.sender,msg.msg)
                    
                for command in bot.getCommands():
                    if command.shouldRespond(msg,bot.getUserLevel(msg.sender)):
                        response = command.respond(msg,sock)
                        if len(response)>0:
                            logMessage(nick,response)
                """
                if msg.messageType == 'PING':
                    sock.sendall(b"PONG "+msg.msg.encode('utf-8')+b"\n")
                """
                if msg.messageType == 'NOTICE':
                    handleNoticeMessage(msg)

                    
        for feature in bot.getFeatures():
            feature.handleFeature(sock)
            

        
        sleep(pollFreq)
    print ("DONE!")
    sock.close()

