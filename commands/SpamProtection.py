import imp
import json
import re
from urllib.request import urlopen
from time import time

baseFile = "astronomibot.py"
if __name__ == "__main__":
    baseFile = "../"+baseFile
    
c = imp.load_source('Command',baseFile)

def grabUrls(text):
    """Given a text string, returns all the urls we can find in it."""
    return url_re.findall(text)


urls = '(?: %s)' % '|'.join("""http telnet gopher file wais
ftp""".split())
ltrs = r'\w'
gunk = r'/#~:.?+=&%@!\-'
punc = r'.:?\-'
any = "%(ltrs)s%(gunk)s%(punc)s" % { 'ltrs' : ltrs,
                                     'gunk' : gunk,
                                     'punc' : punc }

url = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""

url_re = re.compile(url, re.VERBOSE | re.MULTILINE)

class SpamOffender():

    def warn(self):
        self.time = time()

    def timeOut(self):
        self.time = time()
        self.numTimeouts += 1

    def wasWarned(self,period):
        return time()-self.time < period

    def getNumTimeouts(self):
        return self.numTimeouts

    def getName(self):
        return self.name

    def __eq__(self,key):
        return key == self.name
    
    def __init__(self,name):
        self.name = name
        self.time = time()
        self.numTimeouts = 0
        

class SpamProtection(c.Command):

    commonChars=["!","?",","," ","$",".","-","=","(",")","*","&","#",":","/","\\"]
    maxAsciiSpam = 10
    maxEmoteSpam = 10
    timeoutPeriod = 30 #in seconds
    warningPeriod = 300 #In seconds
    offenders = []
    emoteList ={}

    def getParams(self):
        params = []
        params.append({'title':'AsciiLimit','desc':'Number of non-standard characters allowed in a message before the user is warned','val':self.maxAsciiSpam})
        params.append({'title':'EmoteLimit','desc':'Number of emotes allowed in a message before the user is warned','val':self.maxEmoteSpam})
        params.append({'title':'TimeOutPeriod','desc':'Default timeout time for spam offenses','val':self.timeoutPeriod})
        params.append({'title':'WarningPeriod','desc':'Time allowed between "spam" messages before they are timed out','val':self.warningPeriod})

        return params

    def setParam(self, param, val):
        if param == 'AsciiLimit':
            self.maxAsciiSpam = val
        elif param == 'EmoteLimit':
            self.maxEmoteSpam = val
        elif param == 'TimeOutPeriod':
            self.timeoutPeriod = val
        elif param == 'WarningPeriod':
            self.warningPeriod = val

    def asciiSpamCheck(self,msg,userLevel):
        nonAlnumCount=0
        
        if msg.messageType == 'PRIVMSG':
            for char in msg.msg:
                if not char.isalnum():
                    if char not in self.commonChars:
                        nonAlnumCount = nonAlnumCount+1

        return nonAlnumCount

    def emoteSpamCheck(self,msg,userLevel):
        emoteCount = 0
        
        for emote in self.emoteList.keys():
            matches = self.emoteList[emote].findall(msg.msg)
            if len(matches)>0:
                emoteCount = emoteCount + len(matches)

        return emoteCount

    def urlSpamCheck(self,msg,userLevel):
        matchedUrls = grabUrls(msg.msg)
        if msg.messageType == 'PRIVMSG':
            if len(matchedUrls)>0:
                return True
        return False
    
    def shouldRespond(self, msg, userLevel):

        if userLevel != EVERYONE:
            return False
        
        if self.asciiSpamCheck(msg,userLevel)>self.maxAsciiSpam:
            return True

        if self.emoteSpamCheck(msg,userLevel)>self.maxEmoteSpam:
            return True

        if self.urlSpamCheck(msg,userLevel):
            return False


                               
        return False

    def respond(self,msg,sock):
        response = ""
        warnOnly = True
        
        if self.asciiSpamCheck(msg,EVERYONE)>self.maxAsciiSpam:
            response = "Don't spam characters like that, "+msg.sender+"!"
            
        if self.emoteSpamCheck(msg,EVERYONE)>self.maxEmoteSpam:
            response = "Don't spam emotes like that, "+msg.sender+"!"

        if msg.sender in self.offenders:
            offender = self.offenders[self.offenders.index(msg.sender)]
            if offender.wasWarned(self.warningPeriod):
                offender.timeOut()
                timeoutLength = offender.getNumTimeouts() * self.timeoutPeriod
                response = response + " ("+str(timeoutLength)+" second time out)"
                toMsg = "PRIVMSG "+channel+" :/timeout "+offender.getName()+" "+str(timeoutLength)+"\n"
                sock.sendall(toMsg.encode('utf-8'))


            else:
                offender.warn()
                response = response + " (Warning)"
        else:
            offender = SpamOffender(msg.sender)
            self.offenders.append(offender)
            response = response + " (Warning)"
            
            
    

        sockResponse = "PRIVMSG "+channel+" :"+response+"\n"
        sock.sendall(sockResponse.encode('utf-8'))

        return response

    def loadTwitchEmotes(self):
        response = urlopen('https://api.twitch.tv/kraken/chat/emoticons')
        emotes = json.loads(response.read().decode())['emoticons']
        for emote in emotes:
            self.emoteList[emote["regex"]] = re.compile(emote["regex"])

    def __init__(self,bot,name):
        super(SpamProtection,self).__init__(bot,name)
        self.loadTwitchEmotes()

