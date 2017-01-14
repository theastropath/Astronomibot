from astrolib.command import Command
from astrolib import MOD

import json

class ChannelManagement(Command):

    def __init__(self,bot,name):
        super(ChannelManagement,self).__init__(bot,name)
        if not self.bot.isCmdRegistered("!setgame"):
            self.bot.regCmd("!setgame",self)
        else:
            print("!setgame is already registered to ",self.bot.getCmdOwner("!setgame"))

        if not self.bot.isCmdRegistered("!settitle"):
            self.bot.regCmd("!settitle",self)
        else:
            print("!settitle is already registered to ",self.bot.getCmdOwner("!settitle"))

    def getDescription(self, full=False):
        if full:
            return "Moderators can manage the stream title and the game that the channel is listed under"
        else:
            return "Adjust the stream title and game"

    def getState(self):
        tables = []

        cmds = []
        cmds.append(("Command","Description","Example"))
        cmds.append(("!settitle &lt;title&gt;","Sets the stream title to 'title'","!settitle This is a stream about games!"))
        cmds.append(("!setgame &lt;game&gt;","Sets the stream game to 'game'","!setgame Deus Ex"))

        tables.append(cmds)

        return tables

    def getParams(self):
        params = []
        return params

    def setParam(self, param, val):
        pass

    def setGame(self,game):
        DATA = json.dumps({"channel": {"game": game}}).encode("utf-8")
        req = urllib.request.Request(url="https://api.twitch.tv/kraken/channels/72962886", data=DATA, method='PUT')
        req.add_header('Client-ID',self.bot.clientId)
        req.add_header('Accept',"application/vnd.twitchtv.v5+json")
        req.add_header('Authorization',"OAuth "+self.bot.accessToken)
        req.add_header('Content-Type',"application/json")

        try:
            response = urllib.request.urlopen(req)
            stream = response.read().decode()
            streamState = json.loads(stream)
            return True
        except urllib.error.HTTPError as e:
            print (e.read())
        return False

    def setTitle(self,title):
        DATA = json.dumps({"channel": {"status": title}}).encode("utf-8")
        req = urllib.request.Request(url="https://api.twitch.tv/kraken/channels/72962886", data=DATA,method='PUT')
        req.add_header('Client-ID',self.bot.clientId)
        req.add_header('Accept',"application/vnd.twitchtv.v5+json")
        req.add_header('Authorization',"OAuth "+self.bot.accessToken)
        req.add_header('Content-Type',"application/json")

        try:
            response = urllib.request.urlopen(req)
            stream = response.read().decode()
            streamState = json.loads(stream)
            return True
        except urllib.error.HTTPError as e:
            print (e.read())
        return False


    def shouldRespond(self, msg, userLevel):
        if msg.messageType == 'PRIVMSG' and len(msg.msg)!=0 and userLevel>=MOD:
            fullmsg = msg.msg.split()
            if (fullmsg[0]=="!setgame" or fullmsg[0]=="!settitle") and len(fullmsg)>1:
                return True
        return False


    def respond(self,msg,sock):
        fullmsg = msg.msg.split()
        restOfMsg = " ".join(fullmsg[1:])
        textResponse = ""

        #print("Client ID is "+str(self.bot.clientId))
        #print ("Access Token is "+str(self.bot.accessToken))
        if (fullmsg[0]=="!setgame"):
            if (self.setGame(restOfMsg)):
                textResponse = "Setting game to '"+restOfMsg+"'"
            else:
                textResponse = "Failed to change game"
        elif (fullmsg[0]=="!settitle"):
            if (self.setTitle(restOfMsg)):
                textResponse = "Setting stream title to '"+restOfMsg+"'"
            else:
                textResponse = "Failed to change stream title"


        response = "PRIVMSG "+self.bot.channel+" : "+textResponse+"\n"
        sock.sendall(response.encode('utf-8'))

        return textResponse
