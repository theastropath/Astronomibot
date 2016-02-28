import imp
from urllib.request import urlopen
from urllib.error import HTTPError
import json

baseFile = "astronomibot.py"
if __name__ == "__main__":
    baseFile = "../"+baseFile
    
c = imp.load_source('Command',baseFile)

class ChatterList(c.Feature):
    chatListFreq = 120
    chatUpdate = 1
    
    def getParams(self):
        params = []
        params.append({'title':'ChatUpdateFreq','desc':'How frequently the the chatter list should be updated (seconds)','val':self.chatListFreq/2})

        return params

    def setParam(self, param, val):
        if param == 'ChatUpdateFreq':
            self.chatListFreq = val * 2

    
    def handleFeature(self,sock):
        allchatters = []
        self.chatUpdate = self.chatUpdate - 1
        if self.chatUpdate == 0:
            self.chatUpdate = self.chatListFreq
            try:
                response = urlopen('http://tmi.twitch.tv/group/user/'+self.bot.channel[1:]+'/chatters')
                chatters = response.read().decode()
                chatlist = json.loads(chatters)
                for chattertype in chatlist['chatters']:
                    for chatter in chatlist['chatters'][chattertype]:
                        allchatters.append(chatter)
                self.bot.chatters = allchatters
            except HTTPError as e:
                #print("HTTP Error "+str(e.code))
                pass  #Silently accept that this interface will spew 502s all the time
            except:
                print("Some other error when trying to get chatters...")
