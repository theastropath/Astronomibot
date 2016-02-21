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

nick=""
passw=""

pollFreq=0.5
modUpdateFreq = 600 #In units based on the pollFreq
modUpdate = 1
recvAmount=4096

EVERYONE=1
MOD=2
BROADCASTER=3

replaceTerm="$REPLACE"

running = True

modList = [] #List of all moderators for the channel
commands = []
features = []

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

    #Equals is used for checking if the name is in the command list
    def __eq__(self,key):
        return key == self.name

    def __init__(self,name):
        self.name = name

class Feature:
    name = ""

    #This function will go off and do whatever this feature is supposed to do
    def handleFeature(self,sock):
        raise NotImplementedError()

    #Equals is used for checking if the name is in the feature list
    def __eq__(self,key):
        return key == self.name
    
    def __init__(self,name):
        self.name = name


###############################################################################################################    


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


def getModList(channelName):
    #Web method, will keep as a backup, but not used for now
    response = urlopen('http://tmi.twitch.tv/group/user/'+channelName[1:]+'/chatters')
    chatters = response.read().decode()
    return (json.loads(chatters)["chatters"]["moderators"])


def getUserLevel(userName):
    if userName==channel[1:]:
        #print(userName+" identified as broadcaster!")
        return BROADCASTER
    elif userName in modList:
        #print(userName+" identified as a mod!")
        return MOD
    else:
        #print(userName+" identified as a scrub!")
        return EVERYONE

def handleNoticeMessage(msg):
    if "The moderators of this room are:" in msg.msg:
        #List of mods can be updated
        mods = msg.msg.split(": ")[1]
        for mod in mods.split(", "):
            modList.append(mod.strip())

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

    sleep (1) #Wait for responses to roll in

    motd = sock.recv(recvAmount)
    print("---------------------------")
    print (str(motd))
    print("---------------------------")

    sock.setblocking(0)

    modUpdate = 1 #Start at 1 so that it will grab the mod list on the first pass

    return sock

def checkCommandsAndFeatures():
    commandFiles = []
    for command in os.listdir(commandsDir):
        commandName = command[:-3]
        if ".py" in command[-3:] and commandName not in commands:
            commandFiles.append(commandName)

    featureFiles = []  
    for feature in os.listdir(featuresDir):
        featureName = feature[:-3]
        if ".py" in feature[-3:] and featureName not in features:
            featureFiles.append(featureName)

    for command in commandFiles:

        #Load file, and get the corresponding class in it, then instantiate it
        c = imp.load_source('Command',commandsDir+os.sep+command+".py")
        cmd = getattr(c,command)
        
        commands.append(cmd(command))
        print("Loading command module '"+command+"'")
        
    for feature in featureFiles:
        #Load file, and get the corresponding class in it, then instantiate it
        f = imp.load_source('Feature',featuresDir+os.sep+feature+".py")
        feat = getattr(f,feature)
        
        features.append(feat(feature))
        print("Loading feature module '"+feature+"'")


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

    while(running):
        message = ""

        #Get any commands or features
        checkCommandsAndFeatures()
        
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
                    
                for command in commands:
                    if command.shouldRespond(msg,getUserLevel(msg.sender)):
                        response = command.respond(msg,sock)
                        if len(response)>0:
                            logMessage(nick,response)
                """
                if msg.messageType == 'PING':
                    sock.sendall(b"PONG "+msg.msg.encode('utf-8')+b"\n")
                """
                if msg.messageType == 'NOTICE':
                    handleNoticeMessage(msg)

        #Check to see if mod list needs to be updated
        modUpdate = modUpdate - 1
        if modUpdate == 0:
            #Send request
            sock.sendall(b"PRIVMSG "+channel.encode('utf-8')+b" .mods\n")
            modUpdate = modUpdateFreq
        
        sleep(pollFreq)
    print ("DONE!")
    sock.close()

