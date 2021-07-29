from astrolib import *

class IrcMessage:

    def parseTags(self,tags):
        tagDict = {}
        for tag in tags:
            splitTag = tag.split("=",1)
            if len(splitTag)>1 and len(splitTag[1])>0:
                tagName = splitTag[0]
                restOfTag = splitTag[1]
                tagVal = restOfTag
                if tagName == "emotes":
                    #Generate a dictionary giving a list of locations for each emote type
                    emoteList = {}
                    emoteTypes = restOfTag.split("/")
                    for emoteType in emoteTypes:
                        emote = emoteType.split(":")
                        emoteNum = emote[0]
                        emoteLocs = emote[1].split(",")
                        emoteList[emoteNum]=emoteLocs
                    tagVal = emoteList
                elif tagName == "badges" or tagName == "badge-info":
                    badges = restOfTag.split(",")
                    badgeList = []
                    for badge in badges:
                        badgeInfo = badge.split("/")
                        badgeList.append(badgeInfo)
                    tagVal = badgeList
                else:
                    tagVal = restOfTag

                tagDict[tagName]=tagVal
            else:
                tagDict[splitTag[0]]=None
        return tagDict
    
    def __init__(self, message):
        #print(message)
        msgstr = message.rstrip()
        if (msgstr.startswith("PING")):
            breakdown = msgstr.split(None,1)
            messageType = breakdown[0]
            rest = breakdown[1]
            tags = None
            
        elif msgstr[0]=="@":
            breakdown = msgstr.split(None, 3)
            #print("Has tags")
            #Has tags, need to shift everything by one
            tags = breakdown[0]
            prefix = breakdown[1]
            messageType = breakdown[2]
            rest = breakdown[3] if len(breakdown) > 3 else ''
        else:
            #print("Has no tags")
            breakdown = msgstr.split(None, 2)
            tags = None
            prefix = breakdown[0]
            messageType = breakdown[1]
            rest = breakdown[2] if len(breakdown) > 2 else ''

        #To determine what type of message it is, we can simply search
        #for the message type in the message.  However, we also need to
        #make sure it isn't just a user typing in a message type...
        #Therefore, for any type of message other than PRIVMSG, we need
        #to check to see if PRIVMSG is in there as well
        self.messageType = messageType
        self.sender = ''
        self.channel = ''
        self.msg = ''
        self.tags = None

        if tags:
            #Parse tags
            tags = tags[1:] #Strip the @ off the front
            tagList = tags.split(";")
            #print(str(tagList))
            self.tags = self.parseTags(tagList)
            #print(str(self.tags))

        if messageType == 'PRIVMSG':
            breakdown = rest.split(None, 1)
            self.sender = prefix.split('!', 1)[0][1:]
            self.channel = breakdown[0]
            self.msg = breakdown[1][1:] if len(breakdown) > 1 else ''

        elif messageType == 'PING':
            self.msg = rest

        elif messageType == 'NOTICE':
            breakdown = rest.split(None, 1)
            self.sender = prefix[1:]
            self.channel = breakdown[0]
            self.msg = breakdown[1][1:] if len(breakdown) > 1 else ''

        elif messageType == 'JOIN':
            self.sender = prefix.split('!', 1)[0][1:]
            self.channel = rest
            self.msg = rest
        
        elif messageType == 'PART':
            self.sender = prefix.split('!', 1)[0][1:]
            self.channel = rest
            self.msg = rest

        elif messageType == 'CAP':
            breakdown = rest.split(None, 2)
            self.sender = prefix[1:]
            # 'CAP * ACK'
            self.messageType = ' '.join((messageType, breakdown[0], breakdown[1]))
            self.msg = breakdown[2]
        elif messageType == 'HOSTTARGET':
            breakdown = rest.split()
            self.sender = breakdown[0][1:] #Everything past the #, the channel doing the hosting
            self.msg = breakdown[1][1:]   #Everything past the :, the channel being hosted
            if self.msg == '-': #Unhost is marked with a dash for some reason
                self.msg = ''
        elif messageType == 'USERNOTICE':
            breakdown = rest.split(None,1)
            self.sender = 'twitch'
            self.channel = breakdown[0]
            self.msg = breakdown[1][1:] if len(breakdown) > 1 else ''
            
        elif messageType.isdecimal():
            # motd and such
            breakdown = rest.split(None, 1)
            self.receiver = breakdown[0]
            self.sender = prefix[1:]
            self.msg = breakdown[1][1:]

        #else:
        #    print("Other message type: "+messageType)

        if not self.msg:
            self.messageType = 'INVALID'

