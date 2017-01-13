from ..feature import Feature

class ModListUpdate(Feature):

    def __init__(self,bot,name):
        super(ModListUpdate,self).__init__(bot,name)
        self.modUpdateFreq = 600 #In units based on the pollFreq (In astronomibot.py)
        self.modUpdate = 1

    def handleFeature(self,sock):
        #Check to see if mod list needs to be updated
        self.modUpdate = self.modUpdate - 1
        if self.modUpdate == 0:
            #Send request
            sock.sendall(b"PRIVMSG "+self.bot.channel.encode('utf-8')+b" .mods\n")
            self.modUpdate = self.modUpdateFreq
