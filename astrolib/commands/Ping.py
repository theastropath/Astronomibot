from astrolib.command import Command

class Ping(Command):

    def getParams(self):
        params = []
        return params

    def setParam(self, param, val):
        pass

    def shouldRespond(self, msg, userLevel):
        return msg.messageType=="PING"

    def respond(self,msg,sock):
        #print ("Responding to PING")
        #self.bot.addLogMessage("Ping: Connection to Twitch still alive")
        sock.sendall(b"PONG "+msg.msg.encode('utf-8')+b"\n")
        return ""
