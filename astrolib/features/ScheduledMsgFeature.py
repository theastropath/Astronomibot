from astrolib.feature import Feature

class ScheduledMsgFeature(Feature):

    def __init__(self,bot,name):
        super(ScheduledMsgFeature,self).__init__(bot,name)
        self.schedMsgCmd = self.bot.commands["ScheduledMsgCmd"]

    def sendMessage(self,message,sock):
        msg = "PRIVMSG "+self.bot.channel+" :"+message+"\n"
        sock.sendall(msg.encode('utf-8'))

    def handleFeature(self,sock):
        for cmd in self.schedMsgCmd.schedMsgs.keys():
            schedCmd = self.schedMsgCmd.schedMsgs[cmd]
            response = schedCmd.tickMsg()
            if response != "":
                self.sendMessage(response,sock)
