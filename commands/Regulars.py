import imp
baseFile = "astronomibot.py"
if __name__ == "__main__":
    baseFile = "../"+baseFile

c = imp.load_source('Command',baseFile)

configDir = "config"
regFile = "regulars.txt"

class Regulars(c.Command):

    def __init__(self,bot,name):
        super(Regulars,self).__init__(bot,name)
        self.bot = bot

        if not self.bot.isCmdRegistered("!addreg"):
            self.bot.regCmd("!addreg",self)
        else:
            print("!addreg is already registered to ",self.bot.getCmdOwner("!addreg"))

        if not self.bot.isCmdRegistered("!delreg"):
            self.bot.regCmd("!delreg",self)
        else:
            print("!delreg is already registered to ",self.bot.getCmdOwner("!delreg"))

        #Load regulars
        if not os.path.exists(configDir+os.sep+channel[1:]):
            os.makedirs(configDir+os.sep+channel[1:])

        try:
            with open(configDir+os.sep+channel[1:]+os.sep+regFile,encoding='utf-8') as f:
                for line in f:
                    reg = line.strip()
                    self.bot.regulars.append(reg)
        except FileNotFoundError:
            print ("Regulars file is not present")


    def getParams(self):
        params = []

        return params

    def setParam(self, param, val):
        pass

    def getState(self):
        tables = []

        commands = [("Command","Description","Example")]
        commands.append(("!addreg","Adds one or more users as a 'regular viewer'","!addreg "+self.bot.name))
        commands.append(("!delreg","Removes one or more users as a 'regular viewer'","!delreg "+self.bot.name))

        regs = [("User",)]
        for reg in self.bot.regulars:
            regs.append((reg,))


        tables.append(commands)
        tables.append(regs)

        return tables

    def getDescription(self, full=False):
        if full:
            return "Functionality for giving 'regular viewers' higher permission levels to perform commands than those just watching for the first time.  Only usable by moderators or above"
        else:
            return "Managing 'regular viewers'"

    def shouldRespond(self, msg, userLevel):
        if userLevel>=MOD:
            if msg.messageType == 'PRIVMSG' and len(msg.msg)!=0:
                splitMsg = msg.msg.split()
                if splitMsg[0]=='!addreg' and len(splitMsg)>=2:
                    return True
                if splitMsg[0]=='!delreg' and len(splitMsg)>=2:
                    return True

        return False

    def respond(self,msg,sock):
        changed = False
        adding = False
        changelist = []
        nochangelist = []
        splitMsg = msg.msg.split()
        if splitMsg[0] =='!addreg':
            adding=True
            for reg in splitMsg[1:]:
                if reg.lower() in self.bot.regulars:
                    #print (reg+" is already a regular")
                    nochangelist.append(reg)
                else:
                    #print("Trying to add "+reg+" to regs")
                    changed = True
                    changelist.append(reg)
                    self.bot.addLogMessage("Regulars: Adding "+reg+" as a regular")

                    self.bot.regulars.append(reg.lower())
        elif splitMsg[0] == '!delreg':
            for reg in splitMsg[1:]:
                if reg.lower() not in self.bot.regulars:
                    nochangelist.append(reg)
                    #print (reg+" isn't a regular")
                else:
                    #print("Removing "+reg+" from regs")
                    changed = True
                    changelist.append(reg)
                    self.bot.addLogMessage("Regulars: Removing "+reg+" from the regular")

                    self.bot.regulars.remove(reg.lower())


        #Save the new list of regulars
        if changed:
            commands = channel[1:]+cmdFile
            with open(configDir+os.sep+channel[1:]+os.sep+regFile,mode='w',encoding="utf-8") as f:
                for reg in self.bot.regulars:
                    f.write(reg.lower()+"\n")

        response = ""

        if len(changelist)>0:
            response+=", ".join(changelist)
            if len(changelist)>1:
                response+=" were "
            else:
                response+=" was "

            if adding:
                response+="added to "
            else:
                response+="removed from "

            response+="the regulars list.  "

        if len(nochangelist)>0:
            response+=", ".join(nochangelist)
            if len(nochangelist)>1:
                response+=" were "
            else:
                response+=" was "

            if adding:
                response+="already on "
            else:
                response+="not on "

            response+="the regulars list.  "


        ircResponse = "PRIVMSG "+channel+" :"+response+"\n"
        sock.sendall(ircResponse.encode('utf-8'))

        return response
