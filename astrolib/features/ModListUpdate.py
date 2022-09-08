from astrolib.feature import Feature

class ModListUpdate(Feature):

    def __init__(self,bot,name):
        super(ModListUpdate,self).__init__(bot,name)
        self.modUpdateFreq = 600 #In units based on the pollFreq (In astronomibot.py)
        self.modUpdate = 1
        #self.bot.subToNotices(self.handleNotice)

    def handleNotice(self,noticeMsg):
        if noticeMsg.tags and noticeMsg.tags['msg-id']=='room_mods':
            #List of mods can be updated
            mods = noticeMsg.msg.split(": ")[1]
            self.bot.modList = []
            for mod in mods.split(", "):
                self.bot.modList.append(mod.strip())
            return True
        return False

    def handleFeature(self,sock):
        #Check to see if mod list needs to be updated
        self.modUpdate = self.modUpdate - 1
        if self.modUpdate == 0:
            #Send request
            #sock.sendall(b"PRIVMSG "+self.bot.channel.encode('utf-8')+b" .mods\n")
            latestMods=self.bot.api.getModsHelix(self.bot.channelId)
            if latestMods:
                #print(str(latestMods))
                self.bot.modList=latestMods
            self.modUpdate = self.modUpdateFreq
