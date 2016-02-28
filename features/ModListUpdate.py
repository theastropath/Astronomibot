import imp
baseFile = "astronomibot.py"
if __name__ == "__main__":
    baseFile = "../"+baseFile
    
c = imp.load_source('Command',baseFile)

class ModListUpdate(c.Command):
    modUpdateFreq = 600 #In units based on the pollFreq (In astronomibot.py)
    modUpdate = 1

    def __init__(self,bot,name):
        super(ModListUpdate,self).__init__(bot,name)
        self.modUpdate = 1
        
    def handleFeature(self,sock):
        #Check to see if mod list needs to be updated
        self.modUpdate = self.modUpdate - 1
        if self.modUpdate == 0:
            #Send request
            sock.sendall(b"PRIVMSG "+self.bot.channel.encode('utf-8')+b" .mods\n")
            self.modUpdate = self.modUpdateFreq
        
