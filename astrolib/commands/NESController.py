import time
from astrolib.command import Command
import socket

class NESController(Command):
    def __init__(self,bot,name):
        super(NESController,self).__init__(bot,name)
        self.bot = bot

        self.ctrlIP="192.168.1.227"
        self.ctrlPort=1337
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

        if not self.bot.isCmdRegistered("!tap"):
            self.bot.regCmd("!tap",self)
        else:
            print("!tap is already registered to ",self.bot.getCmdOwner("!tap"))


    def getParams(self):
        params = []
        return params

    def setParam(self, param, val):
        pass

    def shouldRespond(self, msg, userLevel):
        if msg.messageType == 'PRIVMSG' and len(msg.msg)!=0:
            splitMsg = msg.msg.split()
            if len(splitMsg)>=2 and splitMsg[0].lower()=='!tap':
                button = splitMsg[1].lower()
                if button=='a' or button=='b' or button=='up' or button=='down' or button=='left' or button=='right' or button=='start' or button=='select':
                    if len(splitMsg)==2:
                        return True
                    elif (len(splitMsg)==3):
                        if splitMsg[2].isdigit() and int(splitMsg[2])<=10:
                            return True

        return False


    def getState(self):
        tables = []

        return tables

    def getDescription(self, full=False):
        if full:
            return "Users can send button presses to an actual NES through a hardware interface"
        else:
            return "Send commands to a virtual NES controller!"
        
    def generateMessage(self,action,button):
        return bytes('{"msgtype":"'+action+'","button":"'+button+'"}',"utf-8")


    def respond(self,msg,sock):
        response = ""

        splitMsg = msg.msg.split()
        
        action = splitMsg[0].lower()[1:]
        button = splitMsg[1].lower()
        times = 1
        if len(splitMsg)==3:
            times = int(splitMsg[2])

        pktmsg=self.generateMessage(action,button)

        for i in range(0,times):
            self.sock.sendto(pktmsg,(self.ctrlIP,self.ctrlPort))
            if times>1:
                time.sleep(0.3)
        
        ircResponse = "PRIVMSG %s :%s\n" % (self.bot.channel, response)
        sock.sendall(ircResponse.encode('utf-8'))

        return response
