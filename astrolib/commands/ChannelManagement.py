from astrolib.command import Command
from astrolib import MOD

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

        cmds = [
            ("Command","Description","Example"),
            ("!settitle <title>","Sets the stream title to 'title'","!settitle This is a stream about games!"),
            ("!setgame <game>","Sets the stream game to 'game'","!setgame Deus Ex")
        ]

        tables.append(cmds)

        return tables

    def getParams(self):
        params = []
        return params

    def setParam(self, param, val):
        pass

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
        if fullmsg[0] == "!setgame":
            if self.bot.api.setGameByIdHelix(self.bot.channelId, restOfMsg):
                textResponse = "Setting game to '"+restOfMsg+"'"
            else:
                textResponse = "Failed to change game"
        elif fullmsg[0] == "!settitle":
            if self.bot.api.setTitleByIdHelix(self.bot.channelId, restOfMsg):
                textResponse = "Setting stream title to '"+restOfMsg+"'"
            else:
                textResponse = "Failed to change stream title"


        response = "PRIVMSG "+self.bot.channel+" : "+textResponse+"\n"
        sock.sendall(response.encode('utf-8'))

        return textResponse
