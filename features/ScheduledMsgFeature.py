import imp
baseFile = "astronomibot.py"
if __name__ == "__main__":
    baseFile = "../"+baseFile
    
c = imp.load_source('Command',baseFile)

class ScheduledMsgFeature(c.Feature):

    def __init__(self,bot,name):
        super(ScheduledMsgFeature,self).__init__(bot,name)
        self.schedMsgCmd = self.bot.commands[self.bot.commands.index("ScheduledMsgCmd")]

    def sendMessage(self,message,sock):
        msg = "PRIVMSG "+self.bot.channel+" :"+message+"\n"
        sock.sendall(msg.encode('utf-8'))

    def handleFeature(self,sock):
        for cmd in self.schedMsgCmd.schedMsgs.keys():
            schedCmd = self.schedMsgCmd.schedMsgs[cmd]
            response = schedCmd.tickMsg()
            if response != "":
                self.sendMessage(response,sock)
                
