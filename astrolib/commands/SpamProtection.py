import re
import time
from astrolib.command import Command
from astrolib import MOD,EVERYONE
from urlextract import URLExtract
import os

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

configDir = "config"
safeFile = "safelist.txt"
blockedWordsFile = "blockedwords.txt"
blockedNamePrefixesFile = "blockednameprefixes.txt"

class SpamOffender:

    def warn(self):
        self.time = time.time()

    def timeOut(self):
        self.time = time.time()
        self.numTimeouts += 1

    def wasWarned(self,period):
        return time.time()-self.time < period

    def getNumTimeouts(self):
        return self.numTimeouts

    def getName(self):
        return self.name

    def __eq__(self,key):
        return key == self.name

    def __init__(self,name):
        self.name = name
        self.time = time.time()
        self.numTimeouts = 0


class SpamProtection(Command):

    def __init__(self, bot, name):
        super(SpamProtection, self).__init__(bot, name)

        self.commonChars = {"!","?",","," ","$",".","-","=","(",")","*","&","#",":","/","\\"}
        self.maxAsciiSpam = 10
        self.maxEmoteSpam = 10
        self.timeoutPeriod = 30 #in seconds
        self.warningPeriod = 300 #In seconds
        self.permitPeriod = 5 #In minutes
        self.offenders = []
        self.emoteList = {}
        self.permitList = {}
        self.safeList = set()
        self.blockedWords = set()
        self.blockedNamePrefixes = set()
        self.compiledPrefixRe = dict()

        self.initConfig()

        self.extractor = URLExtract()
        stopRight = self.extractor.get_stop_chars_right()
        stopLeft = self.extractor.get_stop_chars_left()
        stopRight.add("/")
        stopLeft.add(".")
        self.extractor.set_stop_chars_right(stopRight)
        self.extractor.set_stop_chars_left(stopLeft)

        self.loadBlockedWords()
        self.loadBlockedNamePrefixes()

        #Load safe list
        if not os.path.exists(configDir+os.sep+self.bot.channel[1:]):
            os.makedirs(configDir+os.sep+self.bot.channel[1:])

        try:
            with open(configDir+os.sep+self.bot.channel[1:]+os.sep+safeFile,encoding='utf-8') as f:
                for line in f:
                    safeurl = line.strip()
                    self.safeList.add(safeurl)
        except FileNotFoundError:
            print ("Safe list file is not present")

        if not self.bot.isCmdRegistered("!permit"):
            self.bot.regCmd("!permit",self)
        else:
            print("!permit is already registered to ",self.bot.getCmdOwner("!permit"))
            
        if not self.bot.isCmdRegistered("!addsafe"):
            self.bot.regCmd("!addsafe",self)
        else:
            print("!addsafe is already registered to ",self.bot.getCmdOwner("!addsafe"))

        if not self.bot.isCmdRegistered("!delsafe"):
            self.bot.regCmd("!delsafe",self)
        else:
            print("!delsafe is already registered to ",self.bot.getCmdOwner("!delsafe"))
            
        if not self.bot.isCmdRegistered("!addblockedword"):
            self.bot.regCmd("!addblockedword",self)
        else:
            print("!addblockedword is already registered to ",self.bot.getCmdOwner("!addblockedword"))
            
        if not self.bot.isCmdRegistered("!delblockedword"):
            self.bot.regCmd("!delblockedword",self)
        else:
            print("!delblockedword is already registered to ",self.bot.getCmdOwner("!delblockedword"))

            
        if not self.bot.isCmdRegistered("!addblockedprefix"):
            self.bot.regCmd("!addblockedprefix",self)
        else:
            print("!addblockedprefix is already registered to ",self.bot.getCmdOwner("!addblockedprefix"))
            
        if not self.bot.isCmdRegistered("!delblockedprefix"):
            self.bot.regCmd("!delblockedprefix",self)
        else:
            print("!delblockedprefix is already registered to ",self.bot.getCmdOwner("!delblockedprefix"))

    def initConfig(self):
        if "SpamProtection" not in self.bot.config:
            self.bot.config["SpamProtection"] = {}

        if "maxasciispam" in self.bot.config["SpamProtection"]:
            self.maxAsciiSpam = int(self.bot.config["SpamProtection"]["maxasciispam"])
        else:
            self.bot.config["SpamProtection"]["maxasciispam"] = str(self.maxAsciiSpam)
            
        if "maxemotespam" in self.bot.config["SpamProtection"]:
            self.maxEmoteSpam = int(self.bot.config["SpamProtection"]["maxemotespam"])
        else:
            self.bot.config["SpamProtection"]["maxemotespam"] = str(self.maxEmoteSpam)

        if "timeoutperiod" in self.bot.config["SpamProtection"]:
            self.timeoutPeriod = int(self.bot.config["SpamProtection"]["timeoutperiod"])
        else:
            self.bot.config["SpamProtection"]["timeoutperiod"] = str(self.timeoutPeriod)

        if "warningperiod" in self.bot.config["SpamProtection"]:
            self.warningPeriod = int(self.bot.config["SpamProtection"]["warningperiod"])
        else:
            self.bot.config["SpamProtection"]["warningperiod"] = str(self.warningPeriod)
            
        if "permitperiod" in self.bot.config["SpamProtection"]:
            self.permitPeriod = int(self.bot.config["SpamProtection"]["permitperiod"])
        else:
            self.bot.config["SpamProtection"]["permitperiod"] = str(self.permitPeriod)


    
    def getParams(self):
        params = []
        params.append({'title':'AsciiLimit','desc':'Number of non-standard characters allowed in a message before the user is warned','val':self.maxAsciiSpam})
        params.append({'title':'EmoteLimit','desc':'Number of emotes allowed in a message before the user is warned','val':self.maxEmoteSpam})
        params.append({'title':'TimeOutPeriod','desc':'Default timeout time for spam offenses','val':self.timeoutPeriod})
        params.append({'title':'WarningPeriod','desc':'Time allowed between "spam" messages before they are timed out','val':self.warningPeriod})
        params.append({'title':'PermitPeriod','desc':'Time allowed for a user to post a link after getting a permit','val':self.permitPeriod})
        return params

    def setParam(self, param, val):
        if param == 'AsciiLimit':
            self.maxAsciiSpam = int(val)
        elif param == 'EmoteLimit':
            self.maxEmoteSpam = int(val)
        elif param == 'TimeOutPeriod':
            self.timeoutPeriod = int(val)
        elif param == 'WarningPeriod':
            self.warningPeriod = int(val)
        elif param == 'PermitPeriod':
            self.permitPeriod = int(val)
            
    def getState(self):
        tables = []

        commands = [("Command","Description","Example")]
        commands.append(("!permit [user]","Grants permission to a user to post one link for up to "+str(self.permitPeriod)+" minutes.  (Mod Only)","!permit "+self.bot.name))
        commands.append(("!addsafe [url]","Adds a URL to the safe list, meaning anyone can post that link without a permit.  (Mod Only)","!addsafe google.com"))
        commands.append(("!delsafe [url]","Removes a URL from the safe list, meaning it can no longer be posted without a permit.  (Mod Only)","!delsafe google.com"))
        commands.append(("!addblockedword [word]","Adds a word to the blocklist, which results in an immediate timeout.  (Mod Only)","!addblockedword butt"))
        commands.append(("!delblockedword [word]","Removes a word from the blocklist.  (Mod Only)","!delblockedword butt"))
        commands.append(("!addblockedprefix [word]","Adds a name prefix to the blocklist - Any message from a name matching a blocked prefix is instabanned.  (Mod Only)","!addblockedprefix hoss00312_"))
        commands.append(("!delblockedprefix [word]","Removes a name prefix from the blocklist.  (Mod Only)","!delblockedprefix hoss00312_"))

        safelist = [("URL Safe List",)]
        for url in self.safeList:
            safelist.append((url,))

        blocked = [("# of Blocked Words","# of Blocked Name Prefixes",),(str(len(self.blockedWords)),str(len(self.blockedNamePrefixes)))]

        tables.append(commands)
        tables.append(safelist)
        tables.append(blocked)

        return tables

    def getDescription(self, full=False):
        if full:
            return "Provides protection from ASCII, Emote, and URL spam in chat.  Only people who are not regulars/subscribers/mods will be blocked by this."
        else:
            return "Protects against various types of spam in chat"


    def asciiSpamCheck(self,msg,userLevel):
        nonAlnumCount=0

        if msg.messageType == 'PRIVMSG':
            for char in msg.msg:
                if not char.isalnum():
                    if char not in self.commonChars:
                        nonAlnumCount = nonAlnumCount+1

        return nonAlnumCount

    def saveSafeList(self):
        with open(configDir+os.sep+self.bot.channel[1:]+os.sep+safeFile,mode='w',encoding="utf-8") as f:
            for safeUrl in self.safeList:
                f.write(safeUrl.lower()+"\r\n")
                
    def saveBlockedWords(self):
        with open(configDir+os.sep+self.bot.channel[1:]+os.sep+blockedWordsFile,mode='w',encoding="utf-8") as f:
            for word in self.blockedWords:
                f.write(word.lower()+"\r\n")

    def loadBlockedWords(self):
        try:
            with open(configDir+os.sep+self.bot.channel[1:]+os.sep+blockedWordsFile,encoding='utf-8') as f:
                for line in f:
                    blockword = line.strip()
                    self.blockedWords.add(blockword)
        except FileNotFoundError:
            print ("Blocked Word list file is not present")

    def saveBlockedNamePrefixes(self):
        with open(configDir+os.sep+self.bot.channel[1:]+os.sep+blockedNamePrefixesFile,mode='w',encoding="utf-8") as f:
            for word in self.blockedNamePrefixes:
                f.write(word.lower()+"\r\n")

    def loadBlockedNamePrefixes(self):
        try:
            with open(configDir+os.sep+self.bot.channel[1:]+os.sep+blockedNamePrefixesFile,encoding='utf-8') as f:
                for line in f:
                    blockname = line.strip()
                    self.blockedNamePrefixes.add(blockname)
                    self.compiledPrefixRe[blockname]=re.compile(blockname)

        except FileNotFoundError:
            print ("Blocked Name Prefixes list file is not present")

    def blockedNamePrefixCheck(self,msg,userLevel):
        for prefix in self.blockedNamePrefixes:
            #if msg.sender.lower().startswith(prefix):
            #    return True
            if self.compiledPrefixRe[prefix].match(msg.sender.lower()):
                return True
        return False
    
    def addBlockedPrefix(self,word):
        self.blockedNamePrefixes.add(word)
        self.compiledPrefixRe[word]=re.compile(word)
        self.saveBlockedNamePrefixes()

    def delBlockedPrefix(self,word):
        self.blockedNamePrefixes.remove(word)
        del self.compiledPrefixRe[word]
        self.saveBlockedNamePrefixes()
        
    def blockedWordCheck(self,msg,userLevel):
        for word in self.blockedWords:
            if word.lower() in msg.msg:
                return True
        return False

    def emoteSpamCheck(self,msg,userLevel):
        if msg.tags and 'emotes' in msg.tags and msg.tags["emotes"]!=None:
            emoteCount = 0
            for emoteLocs in msg.tags["emotes"].values():
                emoteCount+=len(emoteLocs)
            return emoteCount
        return 0

    def urlSpamCheck(self,msg,userLevel):
        sender = msg.sender.lower()
        if sender in self.permitList.keys():
            if time.time()-self.permitList[sender] < (self.permitPeriod*60):
                try:
                    del self.permitList[sender]
                except:
                    pass #If it fails...  I don't really care?  It's gone anyway
                return False
            else:
                try:
                    del self.permitList[sender]
                except:
                    pass #If it fails...  I don't really care?  It's gone anyway

        matchedUrls = self.extractor.find_urls(msg.msg,check_dns=True)
        onlySafe = True
        #print(str(self.safeList))
        for url in matchedUrls:
            #print(url)
            if url.lower() not in self.safeList:
                onlySafe = False
                
        if msg.messageType == 'PRIVMSG':
            if not onlySafe:
                return True
        return False     

    def shouldRespond(self, msg, userLevel):

        self.extractor.update_when_older(7)
        
        if msg.messageType == 'PRIVMSG' and len(msg.msg)!=0 and userLevel>=MOD:
            fullmsg = msg.msg.split()
            if fullmsg[0]=="!permit" and len(fullmsg)>1:
                return True
            elif fullmsg[0]=="!addsafe" and len(fullmsg)>1:
                return True
            elif fullmsg[0]=="!delsafe" and len(fullmsg)>1:
                return True
            elif fullmsg[0]=="!addblockedword" and len(fullmsg)>1:
                return True
            elif fullmsg[0]=="!delblockedword" and len(fullmsg)>1:
                return True
            elif fullmsg[0]=="!addblockedprefix" and len(fullmsg)>1:
                return True
            elif fullmsg[0]=="!delblockedprefix" and len(fullmsg)>1:
                return True

        if userLevel != EVERYONE:
            return False

        if msg.messageType!='PRIVMSG':
            return False

        if self.blockedWordCheck(msg,userLevel):
            return True

        if self.blockedNamePrefixCheck(msg,userLevel):
            return True

        if self.asciiSpamCheck(msg,userLevel)>self.maxAsciiSpam:
            return True

        if self.emoteSpamCheck(msg,userLevel)>self.maxEmoteSpam:
            return True

        if self.urlSpamCheck(msg,userLevel):
            return True



        return False

    def respond(self,msg,sock):
        userLevel = self.bot.getUserLevel(msg.sender,msg)
        response = ""
        warnOnly = True
        noWarning = False
        spam = False
        instaban = False

        if userLevel == EVERYONE:
            if self.blockedNamePrefixCheck(msg,userLevel):
                response = "User "+msg.sender+" has a blocked name prefix, instabanning.  If this was a mistake, please send an unban request"
                noWarning = True
                instaban = True
                
            elif self.blockedWordCheck(msg,userLevel):
                response = "We don't like those kinds of words around here, "+msg.sender
                spam = True
                noWarning = True
                
            elif self.asciiSpamCheck(msg,userLevel)>self.maxAsciiSpam:
                response = "Don't spam characters like that, "+msg.sender+"!"
                spam=True

            elif self.emoteSpamCheck(msg,userLevel)>self.maxEmoteSpam:
                response = "Don't spam emotes like that, "+msg.sender+"!"
                spam=True
                
            elif self.urlSpamCheck(msg,userLevel):
                response = "Please don't post links without permission "+msg.sender+"! (You need a !permit)"
                spam=False





            if not instaban:
                if msg.sender in self.offenders:
                    offender = self.offenders[self.offenders.index(msg.sender)]
                    if offender.wasWarned(self.warningPeriod):
                        offender.timeOut()
                        timeoutLength = offender.getNumTimeouts() * self.timeoutPeriod
                        self.bot.addLogMessage("Spam Protection: Timed out "+msg.sender+" for "+str(timeoutLength)+" seconds")
                        response = response + " ("+str(timeoutLength)+" second time out)"
                        toMsg = "PRIVMSG "+self.bot.channel+" :/timeout "+offender.getName()+" "+str(timeoutLength)+"\n"
                        sock.sendall(toMsg.encode('utf-8'))
                        
                    else:
                        if noWarning:
                            offender.timeOut()
                            timeoutLength = offender.getNumTimeouts() * self.timeoutPeriod
                            self.bot.addLogMessage("Spam Protection: Timed out "+msg.sender+" for "+str(timeoutLength)+" seconds")
                            response = response + " ("+str(timeoutLength)+" second time out)"
                            toMsg = "PRIVMSG "+self.bot.channel+" :/timeout "+offender.getName()+" "+str(timeoutLength)+"\n"
                            sock.sendall(toMsg.encode('utf-8'))
                        else:
                            offender.warn()
                            response = response + " (Warning)"
                            toMsg = "PRIVMSG "+self.bot.channel+" :/delete "+msg.tags['id']+"\n"
                            sock.sendall(toMsg.encode('utf-8'))

                else:
                    offender = SpamOffender(msg.sender)
                    self.offenders.append(offender)
                    if noWarning:
                        offender.timeOut()
                        timeoutLength = offender.getNumTimeouts() * self.timeoutPeriod
                        self.bot.addLogMessage("Spam Protection: Timed out "+msg.sender+" for "+str(timeoutLength)+" seconds")
                        response = response + " ("+str(timeoutLength)+" second time out)"
                        toMsg = "PRIVMSG "+self.bot.channel+" :/timeout "+offender.getName()+" "+str(timeoutLength)+"\n"
                        sock.sendall(toMsg.encode('utf-8'))
                    else:
                        offender.warn()
                        response = response + " (Warning)"
                        toMsg = "PRIVMSG "+self.bot.channel+" :/delete "+msg.tags['id']+"\n"
                        sock.sendall(toMsg.encode('utf-8'))

            else:
                #Instaban
                self.bot.addLogMessage("Spam Protection: Instabanned "+msg.sender+" for having a blocked name prefix")
                toMsg = "PRIVMSG "+self.bot.channel+" :/ban "+msg.sender+"\n"
                sock.sendall(toMsg.encode('utf-8'))                


        elif msg.messageType == 'PRIVMSG' and len(msg.msg)!=0 and userLevel>=MOD:
            fullmsg = msg.msg.split()
            if fullmsg[0]=="!permit" and len(fullmsg)>1:
                response = fullmsg[1]+" may post one link for up to "+str(self.permitPeriod)+" minutes"
                self.permitList[fullmsg[1].lower()]=time.time()
                self.bot.addLogMessage("Spam Protection: Granted permit to "+fullmsg[1]+" for "+str(self.permitPeriod)+" minutes")
                #print(str(self.permitList))
            elif fullmsg[0]=="!addsafe" and len(fullmsg)>1:
                response = "Added "+fullmsg[1]+" to the URL safe list"
                self.safeList.add(fullmsg[1].lower())
                self.bot.addLogMessage("Spam Protection: Added "+fullmsg[1]+" to URL safe list")
                self.saveSafeList()
            elif fullmsg[0]=="!delsafe" and len(fullmsg)>1:
                response = "Removed "+fullmsg[1]+" from the URL safe list"
                try:
                    self.safeList.remove(fullmsg[1].lower())
                    self.bot.addLogMessage("Spam Protection: Removed "+fullmsg[1]+" from URL safe list")
                    self.saveSafeList()

                except:
                    response = fullmsg[1]+" was not in the URL safe list"
            elif fullmsg[0]=="!addblockedword" and len(fullmsg)>1:
                word = fullmsg[1].lower()
                if word not in self.blockedWords:
                    response = "Added '"+word+"' to the blocked word list"
                    self.blockedWords.add(word)
                    self.saveBlockedWords()
                else:
                    response = "Word '"+word+"' was already in the blocked word list"
            elif fullmsg[0]=="!delblockedword" and len(fullmsg)>1:
                word = fullmsg[1].lower()
                if word not in self.blockedWords:
                    response = "Word '"+word+"' was not in the blocked word list"
                else:
                    response = "Removed '"+word+"' from the blocked word list"
                    self.blockedWords.remove(word)
                    self.saveBlockedWords()

            elif fullmsg[0]=="!addblockedprefix" and len(fullmsg)>1:
                word = fullmsg[1].lower()
                if word not in self.blockedNamePrefixes:
                    response = "Added '"+word+"' to the blocked name prefix list"
                    self.addBlockedPrefix(word)
                else:
                    response = "Word '"+word+"' was already in the blocked name prefix list"
            elif fullmsg[0]=="!delblockedprefix" and len(fullmsg)>1:
                word = fullmsg[1].lower()
                if word not in self.blockedNamePrefixes:
                    response = "Word '"+word+"' was not in the blocked name prefix list"
                else:
                    response = "Removed '"+word+"' from the blocked name prefix list"
                    self.delBlockedPrefix(word)

                    
            
        sockResponse = "PRIVMSG "+self.bot.channel+" :"+response+"\n"
        sock.sendall(sockResponse.encode('utf-8'))

        return response
