from time import sleep
from socket import *
import json
from urllib.request import urlopen
from datetime import datetime
import os
import sys

twitchIrcServer = "irc.twitch.tv"
twitchIrcPort = 6667
credFile = "creds.txt"
channel = "#theastropath" #Channel name has to be all lowercase
cmdFile = "cmds.txt"
logDir = "logs"

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

customCmds = {} #Dictionary of all custom commands implemented on this bot
modList = [] #List of all moderators for the channel

class CustomCommand:
    command = ""
    response = ""
    userlevel = EVERYONE

    def __init__(self,command,response,userlevel=EVERYONE):
        self.command = command
        self.response = response
        self.userlevel=userlevel

    def canUseCommand(self,userlevel):
        return userlevel>=self.userlevel

    def getResponse(self,msg):
        afterCmd = " ".join(msg.msg.split()[1:]).rstrip()
        if len(afterCmd)>0 and afterCmd[0]=="/":
            afterCmd = ""
        return self.response.replace(replaceTerm,afterCmd)

    def exportCommand(self):
        return self.command+" "+str(self.userlevel)+" "+self.response+'\n'

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

def exportCommands():
    commands = channel[1:]+cmdFile
    f = open(commands,mode='w',encoding="utf-8")
    for cmd in customCmds.keys():
        f.write(customCmds[cmd].exportCommand())
    f.close()
    
def importCommands():
    commands = channel[1:]+cmdFile
    try:
        f = open(commands,encoding="utf-8")
        for line in f:
            command = line.split()[0].lower()
            userLvl = int(line.split()[1])
            response = " ".join(line.split()[2:]).rstrip()
            customCmds[command]=CustomCommand(command,response,userLvl)
        f.close()
    except FileNotFoundError:
        print (commands+" is not present, no commands imported")

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

def addCustomCommand(command):
    newCmd = command.split()[0]
    userLevel=EVERYONE

    if newCmd[0]=="!":
        cmdResp = " ".join(command.split()[1:])
        userLevel=EVERYONE
    else:
        if newCmd == "BROADCASTER":
            newCmd = command.split()[1]
            cmdResp = " ".join(command.split()[2:])
            userLevel=BROADCASTER
        elif newCmd == "MOD":
            newCmd = command.split()[1]
            cmdResp = " ".join(command.split()[2:])
            userLevel=MOD
        elif newCmd == "EVERYONE":
            newCmd = command.split()[1]
            cmdResp = " ".join(command.split()[2:])
            userLevel=EVERYONE
        else:
            return "Invalid user level for command!"

    if cmdResp[0]=="/" or cmdResp[0]==".":
        return "Tut tut, don't try that!"

    newCmd = newCmd.lower()

    if newCmd in customCmds.keys():
        return "Command '"+newCmd+"' already exists!"
    elif len(newCmd)==1:
        return "No command name given!"
    else:
        customCmds[newCmd]=CustomCommand(newCmd,cmdResp,userLevel)
        exportCommands()
        return "Adding "+newCmd+" which will respond with '"+cmdResp+"'"

def editCustomCommand(command):
    newCmd = command.split()[0]
    userLevelChanged = False
    userLevel=EVERYONE

    if newCmd[0]=="!":
        cmdResp = " ".join(command.split()[1:])
        userLevel=EVERYONE
    else:
        userLevelChanged = True
        if newCmd == "BROADCASTER":
            newCmd = command.split()[1]
            cmdResp = " ".join(command.split()[2:])
            userLevel=BROADCASTER
        elif newCmd == "MOD":
            newCmd = command.split()[1]
            cmdResp = " ".join(command.split()[2:])
            userLevel=MOD
        elif newCmd == "EVERYONE":
            newCmd = command.split()[1]
            cmdResp = " ".join(command.split()[2:])
            userLevel=EVERYONE
        else:
            return "Invalid user level for command!"

    if cmdResp[0]=="/" or cmdResp[0]==".":
        return "Tut tut, don't try that!"

    newCmd = newCmd.lower()

    if newCmd in customCmds.keys():
        customCmds[newCmd].response = cmdResp
        if userLevelChanged:
            customCmds[newCmd].userlevel = userLevel
        exportCommands()
        return "Editing "+newCmd+" which will now respond with '"+cmdResp+"'"    
    elif len(newCmd)==1:
        return "No command name given!"
    else:
        return "Command '"+newCmd+"' doesn't exist!"

def delCustomCommand(command):
    cmd = command.split()[0]

    if cmd[0]=="!":
        if cmd in customCmds.keys():
            del customCmds[cmd]
            exportCommands()
            return "Command "+cmd+" has been deleted"
        else:
            return "Command "+cmd+" is not present"
            
    else:
        return  "No command name given!"

def shouldWeRespondToThis(msg,userlevel):
    #For now, we'll only respond to messages starting with !
    if len(msg.msg)== 0:
        return False
    
    if msg.msg[0] == '!':
        command = msg.msg.split()[0].lower() #Only care about the first word
        #Only a few hardcoded commands, then user editable commands
        if command == "!addcom" or command == "!editcom" or command == "!delcom":
            if userlevel>=EVERYONE:
                return True
        elif command == "!stop":
            if userlevel==BROADCASTER:
                return True
        elif command == "!list":
            return True
        else:
            if command in customCmds.keys():
                if customCmds[command].canUseCommand(userlevel):
                    return True
        
    else:
        return False

def respondToThis(msg, sock):
    command = msg.msg.split()[0].lower()
    response = ":"
    if command == "!addcom":
        newCmd = " ".join(msg.msg.split()[1:])
        response = addCustomCommand(newCmd)
        response = "PRIVMSG "+channel+" :"+response+"\n"
        sock.sendall(response.encode('utf-8'))
    elif command == "!editcom":
        newCmd = " ".join(msg.msg.split()[1:])
        response = editCustomCommand(newCmd)
        response = "PRIVMSG "+channel+" :"+response+"\n"
        sock.sendall(response.encode('utf-8'))
    elif command == "!delcom":
        newCmd = " ".join(msg.msg.split()[1:])
        response = delCustomCommand(newCmd)
        response = "PRIVMSG "+channel+" :"+response+"\n"
        sock.sendall(response.encode('utf-8'))
    elif command == "!stop":
        print ("Stopping it!")
        running = False
    elif command == "!list":
        response = ", ".join(customCmds.keys())
        response = "PRIVMSG "+channel+" :"+response+"\n"
        sock.sendall(response.encode('utf-8'))

    else:
        if customCmds[command]:
            response = customCmds[command].getResponse(msg)
            response = "PRIVMSG "+channel+" :"+response+"\n"
            sock.sendall(response.encode('utf-8'))

    #Now strip the IRC formatting off again so that we can log the response
    response = ":".join(response.split(":")[1:])
    response = response[:-1]
    return response

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
    sock.connect((twitchIrcServer,twitchIrcPort))

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
importCommands()

sock = connectToServer()

while(running):
    message = ""
    try:
        message = sock.recv(recvAmount)
    except BlockingIOError:
        pass
    except ConnectionAbortedError:
        print ("Connection got aborted.  Reconnecting")
        sock = connectToServer()

    if message is not "":
        messages = message.decode().rstrip().split("\n")
        for m in messages:
            msg = IrcMessage(m)
            if msg.messageType == 'PRIVMSG':
                logMessage(msg.sender,msg.msg)
                if shouldWeRespondToThis(msg,getUserLevel(msg.sender)):
                    response = respondToThis(msg,sock)
                    logMessage(nick,response)
                    
            elif msg.messageType == 'PING':
                sock.sendall(b"PONG "+msg.msg.encode('utf-8')+b"\n")
                
            elif msg.messageType == 'NOTICE':
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
