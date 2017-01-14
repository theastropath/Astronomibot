import random
from astrolib.command import Command
from astrolib import MOD

class GiveAway(Command):

    def getParams(self):
        params = []
        return params

    def setParam(self, param, val):
        pass

    def getState(self):
        tables = []

        state = []
        state.append(("Setting","Value"))
        state.append(("Giveaway Running",str(self.running)))
        state.append(("Using Keyword?",str(self.usingKeyword)))
        state.append(("Giveaway Keyword",self.keyword))

        cmds = []
        cmds.append(("Command","Description","Example"))
        cmds.append(("start","Starts the giveaway and collects eligible users (Either those who are active in chat, or those who entered the keyword, if applicable)","!giveaway start"))
        cmds.append(("stop","Stops the collection of eligible users","!giveaway stop"))
        cmds.append(("draw","Draws a random user from the list of eligible users.  If done immediately after a reset, it will draw from all users in chat.  If done after starting the giveaway, it will only draw from those who have chatted, or said the keyword (if a keyword is being used)","!giveaway draw"))
        cmds.append(("keyword","Sets the keyword for the giveaway.  Keyword can also be a phrase.  Keyword is not case sensitive", '!giveaway keyword [insert keyword here]'))
        cmds.append(("reset","Resets the eligible users, removes the keyword, and stops the giveaway.","!giveaway reset"))


        eligible = []
        eligible.append(("Eligible Users",))
        if len(self.eligible)>0:
            for user in sorted(self.eligible):
                eligible.append((user,))
        else:
            for chatter in sorted(self.bot.chatters):
                eligible.append((chatter,))
        if (("astronomibot",) in eligible):
            eligible.remove(("astronomibot",))
        tables.append(state)
        tables.append(cmds)
        tables.append(eligible)

        return tables

    def getDescription(self, full=False):
        if full:
            return "Moderators can set up and operate raffles via Astronomibot.  Commands shown are added after a generic '!giveaway' command."
        else:
            return "Run raffles and giveaways!"

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
                        eligible = self.bot.chatters
                    else:
                        #Draw from those in the eligible list
                        eligible = self.eligible

                    if ("astronomibot" in eligible):
                        eligible.remove("astronomibot")
                    winner = random.choice(self.eligible)
                    self.bot.addLogMessage("GiveAway: The winner is "+winner)
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
        self.keyword = ""
        self.eligible = []
        self.usingKeyword = False
        self.running = False
        if not self.bot.isCmdRegistered("!giveaway"):
            self.bot.regCmd("!giveaway",self)
        else:
            print ("!giveaway is already registered to ",self.bot.getCmdOwner("!giveaway"))
