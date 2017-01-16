from astrolib.feature import Feature

class ChatterList(Feature):
    def __init__(self,bot,name):
        super(ChatterList,self).__init__(bot,name)
        self.chatListFreq = 120
        self.chatUpdate = 1

    def getParams(self):
        params = []
        params.append({'title':'ChatUpdateFreq','desc':'How frequently the the chatter list should be updated (seconds)','val':self.chatListFreq/2})

        return params

    def setParam(self, param, val):
        if param == 'ChatUpdateFreq':
            self.chatListFreq = float(val) * 2


    def handleFeature(self,sock):
        self.chatUpdate = self.chatUpdate - 1
        if self.chatUpdate == 0:
            self.chatUpdate = self.chatListFreq
            allchatters = self.bot.api.getAllChatters(self.bot.channel[1:])
            if allchatters is not None:
                self.bot.chatters = allchatters
