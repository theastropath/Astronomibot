import imp
import json
import re
from urllib.request import urlopen

baseFile = "astronomibot.py"
if __name__ == "__main__":
    baseFile = "../"+baseFile
    
c = imp.load_source('Command',baseFile)

class SpamProtection(c.Command):

    commonChars=["!","?",","," ","$",".","-","=","(",")","*","&","#"]
    maxAsciiSpam = 10
    maxEmoteSpam = 10
    emoteList ={}

    def asciiSpamCheck(self,msg,userLevel):
        nonAlnumCount=0
        
        if msg.messageType == 'PRIVMSG':
            for char in msg.msg:
                if not char.isalnum():
                    if char not in self.commonChars:
                        nonAlnumCount = nonAlnumCount+1

        #print ("Found "+str(nonAlnumCount)+" non alphanumeric characters")
        return nonAlnumCount

    def emoteSpamCheck(self,msg,userLevel):
        emoteCount = 0
        
        for emote in self.emoteList.keys():
            matches = self.emoteList[emote].findall(msg.msg)
            if len(matches)>0:
                print(emote+" : Found "+str(len(matches)))
                emoteCount = emoteCount + len(matches)

        return emoteCount

    
    def shouldRespond(self, msg, userLevel):

        if userLevel != EVERYONE:
            return False
        
        if self.asciiSpamCheck(msg,userLevel)>self.maxAsciiSpam:
            print ("Should be responding")
            return True

        if self.emoteSpamCheck(msg,userLevel)>self.maxEmoteSpam:
            print ("Should be responding")
            return True
                               
        return False

    def respond(self,msg,sock):
        response = ""
        if self.asciiSpamCheck(msg,EVERYONE)>self.maxAsciiSpam:
            response = "Don't spam characters like that, "+msg.sender+"!"
            sockResponse = "PRIVMSG "+channel+" :"+response+"\n"
            print(sockResponse)
            sock.sendall(sockResponse.encode('utf-8'))
            
        if self.emoteSpamCheck(msg,EVERYONE)>self.maxEmoteSpam:
            response = "Don't spam emotes like that, "+msg.sender+"!"
            sockResponse = "PRIVMSG "+channel+" :"+response+"\n"
            print(sockResponse)
            sock.sendall(sockResponse.encode('utf-8'))
            
        return response

    def loadTwitchEmotes(self):
        #Web method, will keep as a backup, but not used for now
        response = urlopen('https://api.twitch.tv/kraken/chat/emoticon_images')
        emotes = json.loads(response.read().decode())['emoticons']
        for emote in emotes:
            self.emoteList[emote["code"]] = re.compile(emote["code"])
        print ("Found "+str(len(self.emoteList))+" emotes")

    def __init__(self,name):
        super(SpamProtection,self).__init__(name)
        self.loadTwitchEmotes()

