import imp
import json
import re
from urllib.request import urlopen

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



class SpamProtection(c.Command):

    commonChars=["!","?",","," ","$",".","-","=","(",")","*","&","#",":","/","\\"]
    maxAsciiSpam = 10
    maxEmoteSpam = 10
    emoteList ={}

    def getParams(self):
        params = []
        params.append({'title':'AsciiLimit','desc':'Number of non-standard characters allowed in a message before the user is warned','val':self.maxAsciiSpam})
        params.append({'title':'EmoteLimit','desc':'Number of emotes allowed in a message before the user is warned','val':self.maxEmoteSpam})
        return params

    def setParam(self, param, val):
        if param == 'AsciiLimit':
            self.maxAsciiSpam = val
        elif param == 'EmoteLimit':
            self.maxEmoteSpam = val

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
                #print(emote+" : Found "+str(len(matches)))
                emoteCount = emoteCount + len(matches)

        return emoteCount

    def urlSpamCheck(self,msg,userLevel):
        matchedUrls = grabUrls(msg.msg)
        if msg.messageType == 'PRIVMSG':
            if len(matchedUrls)>0:
                return True
        return False
    
    def shouldRespond(self, msg, userLevel):

        #if userLevel != EVERYONE:
        #    return False
        
        if self.asciiSpamCheck(msg,userLevel)>self.maxAsciiSpam:
            #print ("Should be responding")
            return True

        if self.emoteSpamCheck(msg,userLevel)>self.maxEmoteSpam:
            #print ("Should be responding")
            return True

        if self.urlSpamCheck(msg,userLevel):
            print ("Posted a link...")
            return True


                               
        return False

    def respond(self,msg,sock):
        response = ""
        if self.asciiSpamCheck(msg,EVERYONE)>self.maxAsciiSpam:
            response = "Don't spam characters like that, "+msg.sender+"!"
            sockResponse = "PRIVMSG "+channel+" :"+response+"\n"
            #print(sockResponse)
            sock.sendall(sockResponse.encode('utf-8'))
            
        if self.emoteSpamCheck(msg,EVERYONE)>self.maxEmoteSpam:
            response = "Don't spam emotes like that, "+msg.sender+"!"
            sockResponse = "PRIVMSG "+channel+" :"+response+"\n"
            #print(sockResponse)
            sock.sendall(sockResponse.encode('utf-8'))
            
        return response

    def loadTwitchEmotes(self):
        #Web method, will keep as a backup, but not used for now
        response = urlopen('https://api.twitch.tv/kraken/chat/emoticons')
        emotes = json.loads(response.read().decode())['emoticons']
        for emote in emotes:
            self.emoteList[emote["regex"]] = re.compile(emote["regex"])
        print ("Found "+str(len(self.emoteList))+" emotes")

    def __init__(self,bot,name):
        super(SpamProtection,self).__init__(bot,name)
        self.loadTwitchEmotes()

