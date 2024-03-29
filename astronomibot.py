#!/usr/bin/env python3

from time import sleep
import time
from socket import *
from datetime import datetime
import os
import sys
import traceback
from collections import OrderedDict
import websocket
import json
import threading
from queue import Queue
from configparser import ConfigParser

from astrolib import *
from astrolib.api import TwitchApi
from astrolib.ircmessage import IrcMessage

twitchIrcServer = "irc.twitch.tv"
twitchIrcPort = 6667
credFile = "creds.txt"
credIniFile = "config.ini"
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

def load_module_from_file(module_name, module_path):
    """Loads a python module from the path of the corresponding file.
    Args:
        module_name (str): namespace where the python module will be loaded,
            e.g. ``foo.bar``
        module_path (str): path of the python file containing the module
    Returns:
        A valid module object
    Raises:
        ImportError: when the module can't be loaded
        FileNotFoundError: when module_path doesn't exist
    """
    if sys.version_info[0] == 3 and sys.version_info[1] >= 5:
        import importlib.util
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    elif sys.version_info[0] == 3 and sys.version_info[1] < 5:
        import importlib.machinery
        loader = importlib.machinery.SourceFileLoader(module_name, module_path)
        module = loader.load_module()
    elif sys.version_info[0] == 2:
        import imp
        module = imp.load_source(module_name, module_path)
    return module

###############################################################################################################

class TwitchWebSocketApp(websocket.WebSocketApp):
    def handleChannelPointRedemption(ws,jsonMsg):
        if "type" in jsonMsg:
            #print("Have type: "+str(jsonMsg["type"]))
            if jsonMsg['type']=="reward-redeemed":
                #print("Was a redeemed reward")
                username = ""
                title = ""
                userinput = ""
                channelid = ""
                redemptionId = ""
                rewardId = ""

                if "data" in jsonMsg and "redemption" in jsonMsg["data"]:
                    #print(str(jsonMsg["data"]))
                    red = jsonMsg["data"]["redemption"]
                    if "user" in red and red["user"] and "display_name" in red["user"]:
                        username = red["user"]["display_name"]

                    if "reward" in red and red["reward"]:
                        if "title" in red["reward"]:
                            title = red["reward"]["title"]

                        if "channel_id" in red["reward"]:
                            channelid = red["reward"]["channel_id"]

                        if "id" in red["reward"]:
                            rewardId = red["reward"]["id"]

                    if "user_input" in red and red["user_input"]:
                        userinput = red["user_input"]

                    if "id" in red:
                        redemptionId = red["id"]


                print("Reward was redeemed by "+username+" for: "+title+"   User said: "+userinput)
                qMsg = {"type":NOTIF_CHANNELPOINTS,"data":{"username":username,"reward":title,"message":userinput,"channelid":channelid,"redemptionid":redemptionId,"rewardid":rewardId}}
                try:
                    ws.bot.msgQ.put_nowait(qMsg)
                except Exception as e:
                    print("Failed to put channel point redemption on queue: "+str(e))

    def handleSubscriptionEvent(ws,jsonMsg):
        #print("Was a sub Event")
        username = ""
        if "display_name" in jsonMsg:
            username = jsonMsg["display_name"]
        recipName = ""
        if "recipient_display_name" in jsonMsg:
            recipName = jsonMsg["recipient_display_name"]
        subplan = ""
        if "sub_plan" in jsonMsg:
            subplan = jsonMsg["sub_plan"]
        usermsg = ""
        if "sub_message" in jsonMsg:
            if "message" in jsonMsg["sub_message"]:
                usermsg = jsonMsg["sub_message"]["message"]
        cumMonths = 0
        if "cumulative_months" in jsonMsg:
            cumMonths = jsonMsg["cumulative_months"]
        streakMonths = 0
        if "streak_months" in jsonMsg:
            streakMonths = jsonMsg["streak_months"]
        context = ""
        if "context" in jsonMsg:
            context = jsonMsg["context"]
        print("Got a "+context+" from "+username+" at sub plan "+subplan+" with cumulative/streak months of "+str(cumMonths)+"/"+str(streakMonths)+".  Message: "+usermsg)
        print(str(jsonMsg))
        qMsg = {"type":NOTIF_SUBSCRIPTION,"data":{"username":username,"recipient":recipName,"subplan":subplan,"message":usermsg,"cumulative":cumMonths,"streak":streakMonths,"context":context}}
        try:
            ws.bot.msgQ.put_nowait(qMsg)
        except Exception as e:
            print("Failed to put subscription on queue: "+str(e))
        
    def handleBitsEvent(ws,jsonMsg):
        #print("Was a bits Event")
        if "message_type" in jsonMsg:
            if jsonMsg["message_type"]=="bits_event":
                print("Bits Event")
                if "data" in jsonMsg:
                    username = ""
                    bitsUsed = 0
                    totalBits = 0
                    chatMsg = ""
                    
                    msgData = jsonMsg["data"]
                    if "user_name" in msgData:
                        username = msgData["user_name"]
                    if "bits_used" in msgData:
                        bitsUsed = msgData["bits_used"]
                    if "total_bits_used" in msgData:
                        totalBits = msgData["total_bits_used"]
                    if "chat_message" in msgData:
                        chatMsg = msgData["chat_message"]

                    print(username+" cheered "+str(bitsUsed)+" bits (Total of "+str(totalBits)+" bits) and said: "+chatMsg)
                    qMsg = {"type":NOTIF_BITSEVENT,"data":{"username":username,"bits":bitsUsed,"total":totalBits,"message":chatMsg}}
                    try:
                        ws.bot.msgQ.put_nowait(qMsg)
                    except Exception as e:
                        print("Failed to put bits event on queue: "+str(e))

                    
            else:
                print("Other type: "+jsonMsg["message_type"])
                
    def handlePong(ws,msg):
        #print("Got a Pong")
        ws.last_pong_tm = time.time()

    def handleMessageByType(ws,msg):
        #print(str(msg))
        if "type" in msg:
            if msg["type"]=="MESSAGE":
                if "data" in msg and msg["data"]:
                    msgData = msg["data"]
                    if "topic" in msgData and "message" in msgData:
                        #The "message" is a further JSON message contained within a string
                        jsonMsg = json.loads(msgData["message"])
                        if "channel-points-channel-v1" in msgData["topic"]:
                            ws.handleChannelPointRedemption(jsonMsg)
                        elif "channel-subscribe-events-v1" in msgData["topic"]:
                            ws.handleSubscriptionEvent(jsonMsg)
                        elif "channel-bits-events-v2" in msgData["topic"]:
                            ws.handleBitsEvent(jsonMsg)
                        else:
                            print("Got a different message type")
                            print(str(msgData))
                    else:
                        print("It was a message with Data, but not the expected topic and message fields")
                        print(str(msgData))
            elif msg["type"]=="PONG":
                ws.handlePong(msg)
            elif msg["type"]=="RESPONSE":
                #print(str(msg))
                if "error" in msg:
                    if msg["error"]!="":
                        print("Got error response: "+msg["error"])
            elif msg["type"]=="RECONNECT":
                curTime = datetime.now().ctime()+" "+time.tzname[time.localtime().tm_isdst]
                print(curTime + " - PubSub Websocket sending reconnect request")
            else:
                print("Got something else:")
                print(str(msg))

    
    def generateListenMessage(self):
        message = '{"type":"LISTEN","data":{"topics":["channel-points-channel-v1.'+self.channelId+'","channel-bits-events-v2.'+self.channelId+'", "channel-subscribe-events-v1.'+self.channelId+'"],"auth_token":"'+self.authToken+'"}}'
        return message

    def generatePingMessage(self):
        message = '{"type":"PING"}'
        return message

    def on_open(self,ws):
        curTime = datetime.now().ctime()+" "+time.tzname[time.localtime().tm_isdst]
        print(curTime + " - PubSub Websocket opened")
        msg = ws.generateListenMessage()
        #print("Sending: "+msg)
        ws.send(msg)

    def on_message(self,ws,message):
        #print("Got message")
        jsonMsg = json.loads(message)
        #print(str(jsonMsg))
        ws.handleMessageByType(jsonMsg)

    def on_error(self,ws,error):
        curTime = datetime.now().ctime()+" "+time.tzname[time.localtime().tm_isdst]
        print(curTime + " - PubSub Websocket encountered an error: "+str(error))
        ws.close()

    def on_close(self,ws,close_status,close_msg):
        curTime = datetime.now().ctime()+" "+time.tzname[time.localtime().tm_isdst]
        print(curTime + " - PubSub Websocket closed")

        
    def __init__(self, url, channelId, authToken, bot, header=None,
                 on_open=None, on_message=None, on_error=None,
                 on_close=None, on_ping=None, on_pong=None,
                 on_cont_message=None,
                 keep_running=True, get_mask_key=None, cookie=None,
                 subprotocols=None,
                 on_data=None):
        super(TwitchWebSocketApp,self).__init__(url,header,self.on_open,self.on_message,self.on_error,self.on_close,on_ping,on_pong,on_cont_message,keep_running,get_mask_key,cookie,subprotocols,on_data)
        self.channelId = channelId
        self.authToken = authToken
        self.bot = bot


    
    #Override the standard ping behaviour since Twitch doesn't care about that, but wants an actual PING message instead    
    def _send_ping(self,interval,event,payload):
        while not event.wait(interval):
            if self.last_pong_tm != 0:
                respTime = self.last_pong_tm - self.last_ping_tm
                if respTime > 10: #Twitch says to reconnect if it takes more than 10 seconds to get a pong back
                    print("Took "+str(respTime)+" to get back a PONG")
            self.last_ping_tm = time.time()
            #print("Send ping")
            self.send(self.generatePingMessage())

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

    def pubSubTask(self):
        cycles = 0
        while True:
            self.pubSub.run_forever(ping_interval=180)
            time.sleep(1)
            cycles+=1

            if (cycles==10):
                cycles = 0
                del self.pubSub #Just to make sure
                print("Recreating PubSub socket after 10 reconnects")
                self.pubSub = TwitchWebSocketApp("wss://pubsub-edge.twitch.tv",self.channelId,self.api.accessToken,self)

                

    def subToNotification(self,notifType,callback):
        if notifType not in NOTIF_TYPES:
            print("Can't subscribe to unknown notification type: "+str(notifType))
        else:
            self.notifyList[notifType].append(callback)

    def subToNotices(self,callback):
        self.noticeSubs.append(callback)

    def cachingTask(self):
        while True:

            #The hosted channel undocumented API doesn't work anymore
            #try:
            #    hostedChannel = self.api.getCurrentlyHostedChannel(self.channelId)
            #    if (hostedChannel!=self.hostedChannel):
            #        #Do this separately just to ensure that it is a single set for thread safety
            #        self.hostedChannel = hostedChannel
            #        #print("Now hosting: "+str(hostedChannel))
            #except:
            #    print("Couldn't get hosted channel")
            #    pass #We don't really need to do anything if the lookup fails

            try:
                online = self.api.isStreamOnlineHelix(self.channelName)
                if online!=self.streamOnline:
                    self.streamOnline=online
                        
            except:
                print("Couldn't get stream status")
                pass #A subsequent read will update us

            try:
                allchatters = self.api.getAllChatters(self.channel[1:])
                if allchatters is not None and allchatters:
                    self.chatters = allchatters
            except:
                print("Couldn't get chatter list")
                pass

            sleep(30)


    def __init__(self, config, configFile, pollFreq, api):
        self.modList = [] #List of all moderators for the channel
        self.commands = OrderedDict()
        self.features = OrderedDict()
        self.registeredCmds = []
        self.chatters = []
        self.logs = []
        self.logFile = "ActionLog.txt"
        self.channel = config["Chat"]["channel"]
        self._channelId = None
        self.channelName = config["Chat"]["channel"][1:]
        self.regulars = []
        self.pollFreq = pollFreq
        self.name = config["Chat"]["chatnick"]
        self.api = api
        self.config = config
        self.configFile = configFile

        self.hostedChannel = ""
        self.streamOnline = False
        self.cachingThread = threading.Thread(target=self.cachingTask)
        self.cachingThread.start()

        self.pubSub = TwitchWebSocketApp("wss://pubsub-edge.twitch.tv",self.channelId,self.api.accessToken,self)
        self.pubSubThread = threading.Thread(target=self.pubSubTask)
        self.pubSubThread.start()

        #Modules need to register themselves to receive notifications from PubSub
        #Initialize each notification type as a list for the modules to put themselves into
        self.notifyList = {}
        for notifType in NOTIF_TYPES:
            self.notifyList[notifType]=[]

        #Modules need to register themselves to receive NOTICE messages
        self.noticeSubs = []

        self.msgQ = Queue()
        
        self.importLogs()

    # lazily loaded channel ID
    @property
    def channelId(self):
        if self._channelId is None:
            self._channelId = self.api.getChannelIdHelix()
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
                f.write(log[0]+"$$$"+log[1]+"\r\n")

    def saveConfig(self):
        print("Saving config")
        with open (self.configFile,'w') as configfile:
            self.config.write(configfile)


    def addLogMessage(self,msg):
        curTime = datetime.now().ctime()+" "+time.tzname[time.localtime().tm_isdst]
        self.logs.append((curTime,msg))
        print(curTime+" - "+msg)
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
            chat.append((chatter,userLevelToStr(self.getUserLevel(chatter,None))))
        return chat
    


    def checkCommandsAndFeatures(self):
        commandFiles = []
        gotNew = False
        for command in os.listdir(commandsDir):
            commandName, ext = os.path.splitext(command)
            if ".py" == ext and commandName not in self.commands:
                commandFiles.append(commandName)
                gotNew = True

        featureFiles = []
        for feature in os.listdir(featuresDir):
            featureName, ext = os.path.splitext(feature)
            if ".py" == ext and featureName not in self.features:
                featureFiles.append(featureName)
                gotNew = True

        commandFiles.sort()
        for command in commandFiles:

            #Load file, and get the corresponding class in it, then instantiate it
            c = load_module_from_file('astrolib.commands.'+command, os.path.join(commandsDir, command+".py"))
            try:
                cmd = getattr(c,command)
                self.commands[command] = cmd(self, command)
                print("Loaded command module '"+command+"'")
            except:
                traceback.print_exc()
                print("Couldn't load command module '"+command+"'")

        featureFiles.sort()
        for feature in featureFiles:
            #Load file, and get the corresponding class in it, then instantiate it
            f = load_module_from_file('astrolib.features.'+feature, os.path.join(featuresDir, feature+".py"))
            try:
                feat = getattr(f,feature)
                self.features[feature] = feat(self, feature)
                print("Loaded feature module '"+feature+"'")
            except:
                traceback.print_exc()
                print("Couldn't load feature module '"+feature+"'")

        if gotNew:
            self.saveConfig()


    def getUserLevel(self,userName, msg):
        if msg and msg.tags:  #If we have the actual message, we can figure things out more quickly
            if "room-id" in msg.tags and "user-id" in msg.tags and msg.tags["room-id"]==msg.tags["user-id"]:
                return BROADCASTER
            elif "mod" in msg.tags and msg.tags["mod"]=="1":
                return MOD
            elif "subscriber" in msg.tags and msg.tags["subscriber"]=="1": #If they care enough to give me money, they are probably a regular
                return REGULAR
            elif "badges" in msg.tags and msg.tags["badges"]!=None:
                for badge in msg.tags["badges"]:
                    if badge[0]=="vip":
                        return REGULAR
            

        
        if userName.lower()==self.channel[1:]:
            #print(userName+" identified as broadcaster!")
            return BROADCASTER
        elif userName.lower() in self.modList:
            #print(userName+" identified as a mod!")
            return MOD
        elif userName.lower() in self.regulars:
            return REGULAR
        else:
            #print(userName+" identified as a scrub!")
            return EVERYONE

###############################################################################################################

def handleNoticeMessage(bot,msg):
    handled = False
    for noticeSub in bot.noticeSubs:
        if noticeSub(msg):
            handled = True
    
    if not handled:
        if msg.tags and ('msg-id' in msg.tags):
            print(msg.msg+" (msg-id: "+msg.tags['msg-id']+")")
        else:
            print (msg.msg)

        

def logMessage(sender,msg):
    curTime = datetime.now()
    timestamp = curTime.strftime("%Y-%m-%d %H:%M:%S")
    logFile = curTime.strftime("%Y-%m-%d.txt")
    logMsg = timestamp+" - "+sender+": "+msg+"\r\n"
    channelLogDir = os.path.join(logDir, channel[1:])

    if not os.path.exists(channelLogDir):
        os.makedirs(channelLogDir)

    with open(os.path.join(channelLogDir, logFile), 'a', encoding='utf-8') as f:
        f.write(logMsg)

def connectToServer(channel,nick,passw):
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

#    sock.sendall(
#        b"PASS "+passw.encode('ascii')+b"\n"+
#        b"NICK "+nick.encode('ascii')+b"\n"+
#        b"JOIN "+channel.encode('ascii')+b"\n"+
#        b"CAP REQ :twitch.tv/commands\n"+
#        b"CAP REQ :twitch.tv/tags\n"+
#        b"CAP REQ :twitch.tv/membership\n")
    
    sock.sendall(
        b"CAP REQ :twitch.tv/commands\n"+
        b"CAP REQ :twitch.tv/tags\n"+
        b"CAP REQ :twitch.tv/membership\n"+
        b"PASS "+passw.encode('ascii')+b"\n"+
        b"NICK "+nick.encode('ascii')+b"\n"+
        b"JOIN "+channel.encode('ascii')+b"\n")

    modUpdate = 1 #Start at 1 so that it will grab the mod list on the first pass

    sock.settimeout(pollFreq)

    return sock

def generateNotificationLog(notif):
    message = ""
    if notif["type"]==NOTIF_CHANNELPOINTS:
        message = notif["data"]["username"]+" redeemed "+notif["data"]["reward"]
    elif notif["type"]==NOTIF_SUBSCRIPTION:
        message = "Subscription"
            #username,recipName,subplan,usermsg,cumMonths,streakMonths,context

    if message!="":
        logMessage("Twitch",message)


def convertCredentials(credIni,channel):
    isDefault = True
    if os.path.isfile(credIni):
        #Don't need to convert
        return

    print("Converting credentials to INI file")
    print("Loading basic creds")
    try:
        with open(credFile) as f:
            nick = f.readline().strip('\n')
            passw = f.readline().strip('\n')
            clientId = f.readline().strip('\n')
            clientSecret = f.readline().strip('\n')
            accessToken = f.readline().strip('\n')
            isDefault = False
    except FileNotFoundError:
        print(credFile+" is missing!")
        nick = None
        passw = None
        clientId = None
        clientSecret = None
        accessToken = None

    print("Basic Creds Loaded, trying twitter creds")
    
    try:
        with open("twittercreds.txt") as f:
            twitConsumerkey = f.readline().strip('\n')
            twitConsumersecret = f.readline().strip('\n')
            twitAccesstoken = f.readline().strip('\n')
            twitAccesstokensecret = f.readline().strip('\n')
            isDefault = False

    except FileNotFoundError:
        print("Couldn't find twitter creds")
        twitConsumerkey = None
        twitConsumersecret = None
        twitAccesstoken = None
        twitAccesstokensecret = None
        
    print("Finished with twitter creds, trying Discord creds")

    try:
        with open("discordcreds.txt") as f:
            discordClientId = f.readline().strip('\n')
            discordClientSecret = f.readline().strip('\n')
            discordUserName = f.readline().strip('\n')
            discordUserId = f.readline().strip('\n')
            discordAccessToken = f.readline().strip('\n')
            discordChannelId = f.readline().strip("\n")
            isDefault = False

    except FileNotFoundError:
        print("Couldn't find discord creds")
        discordClientId = None
        discordClientSecret = None
        discordUserName = None
        discordUserId = None
        discordAccessToken = None
        discordChannelId = None

    print("Finished with discord creds, trying ftp creds")

    try:
        with open("ftpcreds.txt") as f:
            ftpUrl = f.readline().strip('\n')
            ftpUser = f.readline().strip('\n')
            ftpPass = f.readline().strip('\n')
            ftpDir = f.readline().strip('\n')
            isDefault = False

    except FileNotFoundError:
        print("Couldn't find ftp creds")
        ftpUrl = None
        ftpUser = None
        ftpPass = None
        ftpDir = None

    print("Finished with FTP creds, trying gamevote creds")

    try:
        with open("gamevotecreds.txt") as f:
            gvapiKey = f.readline().strip("\n")
            gvsheetId = f.readline().strip("\n")
            gvgameSheetName = f.readline().strip("\n")
            gvgameColumn = f.readline().strip("\n")
            gvstatusColumn = f.readline().strip("\n")
            gvfirstGameRow = int(f.readline().strip("\n"))
            gvrandoSheetName = f.readline().strip("\n")
            gvrandoGameColumn = f.readline().strip("\n")
            gvrandoStatusColumn = f.readline().strip("\n")
            gvfirstRandoRow = int(f.readline().strip("\n"))
            isDefault = False

    except:
        print("Couldn't read gamevote creds")
        gvapiKey = None
        gvsheetId = None
        gvgameSheetName = None
        gvgameColumn = None
        gvstatusColumn = None
        gvfirstGameRow = None
        gvrandoSheetName = None
        gvrandoGameColumn = None
        gvrandoStatusColumn = None
        gvfirstRandoRow = None

    print("All creds read")

    config = ConfigParser()

    config["Chat"] = {"ChatNick":nick,
                      "ChatPassword":passw,
                      "Channel":channel}
    
    config["TwitchAPI"] = {"ClientId":clientId,
                           "clientSecret":clientSecret,
                           "AccessToken":accessToken}
    
    config["FTP"] = {"FTPUrl":ftpUrl,
                     "FTPDir":ftpDir,
                     "FTPUser":ftpUser,
                     "FTPPassword":ftpPass}
    
    config["Discord"] = {"ClientId":discordClientId,
                         "ClientSecret":discordClientSecret,
                         "AccessToken":discordAccessToken,
                         "UserName":discordUserName,
                         "UserId":discordUserId,
                         "ChannelId":discordChannelId}

    config["Twitter"] = {"ConsumerKey":twitConsumerkey,
                         "ConsumerSecret":twitConsumersecret,
                         "AccessToken":twitAccesstoken,
                         "AccessTokenSecret":twitAccesstokensecret}

    config["GameVote"] = {"GoogleDocApiKey":gvapiKey,
                          "GoogleSheetId":gvsheetId}

    config["GameVoteTableGame"] =    {"SheetName":gvgameSheetName,
                                      "GameNameColumn":gvgameColumn,
                                      "GameStatusColumn":gvstatusColumn,
                                      "FirstGameRow":gvfirstGameRow}

    config["GameVoteTableRando"] = {"SheetName":gvrandoSheetName,
                                    "GameNameColumn":gvrandoGameColumn,
                                    "GameStatusColumn":gvrandoStatusColumn,
                                    "FirstGameRow":gvfirstRandoRow}

    with open(credIni,mode='w') as f:
        config.write(f)
        
    if isDefault:
        print("No credential files were read, config file is blank!")
        
    print("Config file generated at "+credIni)


    


if __name__ == "__main__":
   
    #Use channel name provided (IF one was provided)
    if len(sys.argv)>1:
        channel = sys.argv[1].lower()
        if channel[0]!='#':
            channel = '#'+channel
        print ("Connecting to provided channel '"+channel+"'")
    else:
        print ("Connecting to default channel '"+channel+"'")

    configfile = configDir+os.sep+channel[1:]+os.sep+credIniFile

    convertCredentials(configfile,channel)

    config = ConfigParser()
    try:
        with open(configfile) as f:
            config.read_file(f)
    except:
        print(configfile+" is missing!")
        exit(1)

    #Check to see if config is blank
    isBlank = True
    for section in config.sections():
        for option in config.options(section):
            if option != "":
                isBlank = False
                break

    if isBlank:
        print("Config file is empty, please fill it in!")
        exit(1)

    sock = connectToServer(config["Chat"]["channel"],
                           config["Chat"]["chatnick"],
                           config["Chat"]["chatpassword"])

    api = TwitchApi(config["TwitchAPI"]["clientid"],
                    config["TwitchAPI"]["accesstoken"],
                    config["TwitchAPI"]["clientsecret"])
    
    bot = Bot(config,
              configfile,
              pollFreq,
              api)
    
    nick = config["Chat"]["chatnick"]
    leftover = bytes()
    commandCheck=0

    while running:
        data = None
        timestamp = datetime.now().ctime()+" "+time.tzname[time.localtime().tm_isdst]

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
            print (timestamp+" "+"Connection got aborted.  Reconnecting")
            sock = connectToServer(config["Chat"]["channel"],
                           config["Chat"]["chatnick"],
                           config["Chat"]["chatpassword"])
        except ConnectionResetError:
            print (timestamp+" "+"Connection got forced closed.  Reconnecting")
            sock = connectToServer(config["Chat"]["channel"],
                                   config["Chat"]["chatnick"],
                                   config["Chat"]["chatpassword"])
        except Exception as e:
            print (timestamp+" "+"Encountered exception '"+str(e.__class__.__name__)+"' while reading")
            sock = connectToServer(config["Chat"]["channel"],
                                   config["Chat"]["chatnick"],
                                   config["Chat"]["chatpassword"])


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
                elif msg.messageType == 'HOSTTARGET':
                    bot.hostedChannel = msg.msg
                    print("Hosting channel "+bot.hostedChannel)
                elif msg.messageType == 'USERNOTICE':
                    notice = ""
                    if (msg.tags):
                        if 'system-msg' in msg.tags:
                            notice+=msg.tags['system-msg'].replace("\\s"," ")
                            notice+=": "
                    notice += msg.msg
                    logMessage(msg.sender,notice)
                    
                    


                for command in bot.getCommands():
                    if command.shouldRespond(msg,bot.getUserLevel(msg.sender,msg)):
                        try:
                            response = command.respond(msg,sock)
                        except BrokenPipeError:
                            print (timestamp+" "+"Broken pipe while responding to command.  Reconnecting")
                            sock = connectToServer(config["Chat"]["channel"],
                                                   config["Chat"]["chatnick"],
                                                   config["Chat"]["chatpassword"])
                        except Exception as e:
                            print (timestamp+" "+"Encountered exception '"+str(e.__class__.__name__)+"' while handling command "+str(command.name)+" handling message '"+str(msg.msg)+"'")
                            traceback.print_exc()
                            sock = connectToServer(config["Chat"]["channel"],
                                                   config["Chat"]["chatnick"],
                                                   config["Chat"]["chatpassword"])

                        if len(response)>0:
                            logMessage(nick,response)

                if msg.messageType == 'NOTICE':
                    handleNoticeMessage(bot,msg)

        while not bot.msgQ.empty():
            #Handle all messages in queue
            qMsg = None
            try:
                qMsg = bot.msgQ.get_nowait()
            except:
                #I guess it actually was empty
                pass

            if qMsg and "type" in qMsg:
                
                if qMsg["type"] not in NOTIF_TYPES:
                    print(timestamp+" "+"Received unknown notification type: "+str(notifType))
                else:
                    generateNotificationLog(qMsg)
                    #Modules have to subscribe to notifications by type using bot.subToNotification
                    for listener in bot.notifyList[qMsg["type"]]:
                        try:
                            response = listener(qMsg["data"],sock)

                            if response:
                                logMessage(nick,response)
                                
                        except BrokenPipeError:
                            print (timestamp+" "+"Broken pipe while handling notification.  Reconnecting")
                            sock = connectToServer(config["Chat"]["channel"],
                                                   config["Chat"]["chatnick"],
                                                   config["Chat"]["chatpassword"])
                        except Exception as e:
                            print (timestamp+" "+"Encountered exception '"+str(e.__class__.__name__)+"' while handling notification ")
                            traceback.print_exc()
                            sock = connectToServer(config["Chat"]["channel"],
                                                   config["Chat"]["chatnick"],
                                                   config["Chat"]["chatpassword"])

        for feature in bot.getFeatures():
            starttime = time.time()
            try:
                feature.handleFeature(sock)
            except BrokenPipeError:
                print ("Broken pipe while handling feature.  Reconnecting")
                sock = connectToServer(config["Chat"]["channel"],
                                       config["Chat"]["chatnick"],
                                       config["Chat"]["chatpassword"])
            except Exception as e:
                print ("Encountered exception '"+str(e.__class__.__name__)+"' while handling feature "+str(feature.name))
                traceback.print_exc()
                sock = connectToServer(config["Chat"]["channel"],
                                       config["Chat"]["chatnick"],
                                       config["Chat"]["chatpassword"])
            totalTime=time.time()-starttime
            #Profiling feature execution time
            if totalTime > 1.5:
                print(timestamp+" "+str(feature)+" took "+str(totalTime)+" seconds")




    print ("DONE!")
    sock.close()
