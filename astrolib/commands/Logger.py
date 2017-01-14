from astrolib.command import Command
from astrolib import MOD

class Logger(Command):

    def __init__(self,bot,name):
        super(Logger,self).__init__(bot,name)
        if not self.bot.isCmdRegistered("!log"):
            self.bot.regCmd("!log",self)
        else:
            print("!log is already registered to ",self.bot.getCmdOwner("!log"))


    def getParams(self):
        params = []
        return params

    def setParam(self, param, val):
        pass

    def getDescription(self, full=False):
        if full:
            return "A logger that keeps track of notable events.  It is also possible for a moderator to insert notes manually"
        else:
            return "Event Logging"

    def getState(self):
        tables = []

        cmds = [("Command", "Description")]
        cmds.append(("!log","Adds a log message to the rolling Astronomibot logger (Only usable by mods or the broadcaster)"))

        logs = [("Time","Log Message")]
        for msg in self.bot.logs:
            logs.append(msg)

        tables.append(cmds)
        tables.append(logs)

        return tables

    def shouldRespond(self, msg, userLevel):
        if msg.messageType == 'PRIVMSG' and len(msg.msg)!=0 and userLevel>=MOD:
            fullmsg = msg.msg.split()
            if fullmsg[0]=="!log" and len(fullmsg)>1:
                return True
        return False

    def respond(self,msg,sock):
        fullmsg = msg.msg.split()
        logMsg = " ".join(fullmsg[1:])
        self.bot.addLogMessage(logMsg)

        response = "PRIVMSG "+self.bot.channel+" : Added log message\n"
        sock.sendall(response.encode('utf-8'))

        return "Added log message"
