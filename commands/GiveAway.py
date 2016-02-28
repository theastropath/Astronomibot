import imp
import random
baseFile = "astronomibot.py"
if __name__ == "__main__":
    baseFile = "../"+baseFile
    
c = imp.load_source('Command',baseFile)

class GiveAway(c.Command):
    keyword = ""
    eligible = []
    usingKeyword = False
    running = False

    def getParams(self):
        params = []
        return params

    def setParam(self, param, val):
        pass

    def getGiveAwayHelp(self):
        response = "Set a giveaway keyword with '!giveaway keyword <phrase>', then start with '!giveaway start'.  Anyone who types the keyword will be entered.  Draw a winner with '!giveaway draw'.  Can also do 'reset' and 'stop'"
        return response
    
    def shouldRespond(self, msg, userLevel):

        if self.running:
            if self.usingKeyword:
                if self.keyword in msg.msg.lower():
                    return True
            else:
                return True
        
        if msg.messageType == 'PRIVMSG' and len(msg.msg)!=0:
            if msg.msg[0]=='!':
                command = msg.msg.split()[0].lower()
                if command == "!giveaway":
                    if userLevel <MOD:
                        return False
                    return True
        return False

    def respond(self,msg,sock):
        fullCmd = msg.msg.lower().split()
        response = ""
        addToList = False

        if self.running:
            if self.usingKeyword:
                if self.keyword in msg.msg.lower():
                    addToList = True
            else:
                addToList = True

        if addToList:
            if msg.sender not in self.eligible:
                self.eligible.append(msg.sender)
            

        if fullCmd[0]=="!giveaway":
            if len(fullCmd) < 2:
                response = self.getGiveAwayHelp()
            else:
                if fullCmd[1] == "start":
                    self.running = True
                    response = "Giveaway: Starting giveaway!"
                elif fullCmd[1] == "stop":
                    self.running = False
                    response = "Giveaway: Stopping giveaway"
                elif fullCmd[1] == "draw":
                    winner = ""
                    if len(self.eligible)==0:
                        #Draw from all chatters
                        winner = random.choice(self.bot.chatters)
                    else:
                        #Draw from those in the eligible list
                        winner = random.choice(self.eligible)

                    response = "Giveaway: The winner is "+winner+"!"
                elif fullCmd[1] == "reset":
                    self.keyword = ""
                    self.usingKeyword = False
                    self.eligible = []
                    self.running = False
                    response = "Giveaway: Resetting giveaway"
                elif fullCmd[1] == "keyword":
                    if len (fullCmd) < 3:
                        self.keyword = ""
                        self.usingKeyword = False
                        response = "Giveaway: No longer using keyword"
                        self.eligible = []
                    else :
                        self.keyword = " ".join(fullCmd[2:])
                        self.usingKeyword = True
                        response = "Giveaway: New keyword is '"+self.keyword+"'"
                        self.eligible = []
                else:
                    response = self.getGiveAwayHelp()

        sockMsg = "PRIVMSG "+self.bot.channel+" :"+response+"\n"
        sock.sendall(sockMsg.encode('utf-8'))
        return response

    def __init__(self,bot,name):
        super(GiveAway,self).__init__(bot,name)

        if not self.bot.isCmdRegistered("!giveaway"):
            self.bot.regCmd("!giveaway",self)
        else:
            print ("!giveaway is already registered to ",self.bot.getCmdOwner("!giveaway"))
        
    
        
