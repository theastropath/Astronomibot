import re
from astrolib.command import Command
from astrolib import \
    EVERYONE, MOD, REGULAR, BROADCASTER, userLevelToStr, \
    replaceTerm, countTerm, referenceCountTerm

cmdFile = "cmds.txt"

referenceCountTermRegEx = re.compile(re.escape(referenceCountTerm) + r'\(([^\(\)]*)\)')


class CustomCommand:

    def __init__(self,allCmds,command,response,callcount=0,userlevel=EVERYONE):
        self.allCmds = allCmds
        self.command = command
        self.response = response
        self.userlevel=userlevel
        self.callcount=callcount

    def canUseCommand(self,userlevel):
        return userlevel>=self.userlevel

    def replaceFunc(self, match):
        commandName = match.group(1)
        if commandName in self.allCmds.customCmds:
            refCount = self.allCmds.customCmds[commandName].callcount
        else:
            refCount = 0
        return str(refCount)

    def handleVariables(self,afterCmd):
        response = self.response
        response = response.replace(replaceTerm,afterCmd)
        response = response.replace(countTerm,str(self.callcount))

        response = referenceCountTermRegEx.sub(self.replaceFunc, response)

        if "CustomApi" in self.allCmds.bot.commands:
            customApi = self.allCmds.bot.commands[self.allCmds.bot.commands.index("CustomApi")]
            for api in customApi.customApis:
                silentApi = "$SILENTAPI("+api+")"
                replaceApi = "$CUSTOMAPI("+api+")"

                if silentApi in response or replaceApi in response:
                    apiResponse = customApi.customApis[api].getApiResponse(afterCmd)
                    response = response.replace(silentApi,"")
                    response = response.replace(replaceApi,apiResponse)

        return response

    def getResponse(self,msg):
        self.callcount+=1
        afterCmd = " ".join(msg.msg.split()[1:]).rstrip()
        if len(afterCmd)>0 and afterCmd[0]=="/":
            afterCmd = ""

        return self.handleVariables(afterCmd)

    def __eq__(self,key):
        return key == self.command

    def __lt__(self,other):
        return other < self.command

    def exportCommand(self):
        return self.command+" "+str(self.userlevel)+" "+str(self.callcount)+" "+self.response+'\n'




class CustomCmds(Command):

    def exportCommands(self):
        commands = self.bot.channel[1:]+cmdFile
        with open(commands,mode='w',encoding="utf-8") as f:
            for cmd in self.customCmds.keys():
                f.write(self.customCmds[cmd].exportCommand())

    def importCommands(self):
        commands = self.bot.channel[1:]+cmdFile
        try:
            with open(commands,encoding="utf-8") as f:
                for line in f:
                    command = line.split()[0].lower().strip()
                    userLvl = int(line.split()[1])

                    callcount=0
                    if line.split()[2].isdigit():
                        callcount = int(line.split()[2])
                        response = " ".join(line.split()[3:]).rstrip()
                    else:
                        response = " ".join(line.split()[2:]).rstrip()

                    if not self.bot.isCmdRegistered(command):
                        self.bot.regCmd(command,self)
                        self.customCmds[command]=CustomCommand(self,command,response,callcount,userLvl)
                    else:
                        print(command,"is already registered to ",self.bot.getCmdOwner(command))

        except FileNotFoundError:
            print (commands+" is not present, no commands imported")

    def addCustomCommand(self,command):
        if len(command)==0:
            return "No command name given"

        newCmd = command.split()[0]
        userLevel=EVERYONE

        if newCmd[0]=="!":
            cmdResp = " ".join(command.split()[1:])
            userLevel=EVERYONE
        else:
            if newCmd == "BROADCASTER":
                newCmd = command.split()[1]
                cmdResp = " ".join(command.split()[2:])
                userLevel=BROADCASTER
            elif newCmd == "MOD":
                newCmd = command.split()[1]
                cmdResp = " ".join(command.split()[2:])
                userLevel=MOD
            elif newCmd == "REGULAR":
                newCmd = command.split()[1]
                cmdResp = " ".join(command.split()[2:])
                userLevel=REGULAR
            elif newCmd == "EVERYONE":
                newCmd = command.split()[1]
                cmdResp = " ".join(command.split()[2:])
                userLevel=EVERYONE
            else:
                return "Invalid user level for command!"
        if len(cmdResp)==0:
            return "No command response given"

        if cmdResp[0]=="/" or cmdResp[0]==".":
            return "Tut tut, don't try that!"

        newCmd = newCmd.lower()

        if self.bot.isCmdRegistered(newCmd):
            return "Command '"+newCmd+"' already exists!"
        elif len(newCmd)==1:
            return "No command name given!"
        else:
            self.customCmds[newCmd]=CustomCommand(self,newCmd,cmdResp,userLevel)
            self.bot.regCmd(newCmd,self)
            self.exportCommands()
            self.bot.addLogMessage("CustomCmds: Added command "+newCmd)
            return "Adding "+newCmd+" which will respond with '"+cmdResp+"'"

    def editCustomCommand(self,command):
        if len(command)==0:
            return "No command name given"
        newCmd = command.split()[0]
        userLevelChanged = False
        userLevel=EVERYONE

        if newCmd[0]=="!":
            cmdResp = " ".join(command.split()[1:])
            userLevel=EVERYONE
        else:
            userLevelChanged = True
            if newCmd == "BROADCASTER":
                newCmd = command.split()[1]
                cmdResp = " ".join(command.split()[2:])
                userLevel=BROADCASTER
            elif newCmd == "MOD":
                newCmd = command.split()[1]
                cmdResp = " ".join(command.split()[2:])
                userLevel=MOD
            elif newCmd == "EVERYONE":
                newCmd = command.split()[1]
                cmdResp = " ".join(command.split()[2:])
                userLevel=EVERYONE
            else:
                return "Invalid user level for command!"

        if cmdResp[0]=="/" or cmdResp[0]==".":
            return "Tut tut, don't try that!"

        newCmd = newCmd.lower()

        if newCmd in self.customCmds.keys():
            self.customCmds[newCmd].response = cmdResp
            if userLevelChanged:
                self.customCmds[newCmd].userlevel = userLevel
            self.exportCommands()
            self.bot.addLogMessage("CustomCmds: Edited command "+newCmd)
            return "Editing "+newCmd+" which will now respond with '"+cmdResp+"'"
        elif len(newCmd)==1:
            return "No command name given!"
        else:
            return "Command '"+newCmd+"' doesn't exist!"

    def delCustomCommand(self,command):
        if len(command)==0:
            return "No command name given"
        cmd = command.split()[0]

        if cmd[0]=="!":
            if cmd in self.customCmds.keys():
                del self.customCmds[cmd]
                self.bot.unregCmd(cmd)
                self.exportCommands()
                self.bot.addLogMessage("CustomCmds: Deleted command "+cmd)
                return "Command "+cmd+" has been deleted"
            else:
                return "Command "+cmd+" is not present"

        else:
            return  "No command name given!"

    def resetCustomCommandCount(self,command):
        if len(command)==0:
            return "No command name given"
        cmd = command.split()[0]
        newCount = 0
        if len(command.split())>1:
            if command.split()[1].isdigit():
                newCount = int(command.split()[1])

        if cmd[0]=="!":
            if cmd in self.customCmds.keys():
                self.customCmds[cmd].callcount=newCount
                self.bot.addLogMessage("CustomCmds: Reset count on "+cmd)
                return "Command "+cmd+" call count has been reset to "+str(newCount)
            else:
                return "command "+cmd+" does not exist"

        else:
            return "No command name given!"

    def getParams(self):
        params = [{'title':'ModComLevel','desc':'What user level do you need to be to edit commands','val':self.modComLevel}]
        return params

    def setParam(self, param, val):
        if param == 'ModComLevel':
            self.modComLevel = int(val)

    def getState(self):
        tables = []
        state = []
        defaults = []
        defaults.append(("Command Name","Description", "User Level"))
        defaults.append(("!addcom",'Add a command to Astronomibot.  Format: "!addcom [userLevel] [response]" ',userLevelToStr(self.modComLevel)))
        defaults.append(("!editcom",'Edits an existing command in Astronomibot.  Format: "!editcom [userLevel] [response]" ',userLevelToStr(self.modComLevel)))
        defaults.append(("!delcom",'Removes a command from Astronomibot.  Format: "!delcom [command]" ',userLevelToStr(self.modComLevel)))
        defaults.append(("!list",'Returns a list of all custom commands in chat',userLevelToStr(self.modComLevel)))
        defaults.append(("!resetcount",'Resets the use count of a command.  Format: "!resetcount [command] [new count]"',userLevelToStr(self.modComLevel)))


        state.append(("Command Name","Description", "User Level", "Use Count"))

        allCmds = []
        for cmd in sorted(self.customCmds.keys()):
            allCmds.append(self.customCmds[cmd])

        for cmd in allCmds:
            state.append((cmd.command,cmd.response,userLevelToStr(cmd.userlevel),str(cmd.callcount)))

        tables.append(defaults)
        tables.append(state)

        return tables

    def getDescription(self, full=False):
        if full:
            return "A module that allows users to create their own commands.  \n$REPLACE will be replaced with anything after the command name.\n$COUNT will be replaced with the number of times the command has been used\n$REF(!cmd) will be replaced with the number of times !cmd has been used"
        else:
            return "User-defined commands"

    def shouldRespond(self, msg, userLevel):
        if msg.messageType == 'PRIVMSG' and len(msg.msg)!=0:
            if msg.msg[0]=='!':
                command = msg.msg.split()[0].lower() #Only care about the first word
                #Only a few hardcoded commands, then user editable commands
                if command == "!addcom" or command == "!editcom" or command == "!delcom" or command == "!resetcount":
                    if userLevel>=self.modComLevel:
                        return True
                elif command == "!list":
                    return True
                else:
                    if command in self.customCmds.keys():
                        if self.customCmds[command].canUseCommand(userLevel):
                            return True

        return False

    def respond(self,msg,sock):
        command = msg.msg.split()[0].lower()
        response = ":"
        if command == "!addcom":
            newCmd = " ".join(msg.msg.split()[1:])
            response = self.addCustomCommand(newCmd)
            response = "PRIVMSG "+self.bot.channel+" :"+response+"\n"
            sock.sendall(response.encode('utf-8'))
        elif command == "!editcom":
            newCmd = " ".join(msg.msg.split()[1:])
            response = self.editCustomCommand(newCmd)
            response = "PRIVMSG "+self.bot.channel+" :"+response+"\n"
            sock.sendall(response.encode('utf-8'))
        elif command == "!delcom":
            newCmd = " ".join(msg.msg.split()[1:])
            response = self.delCustomCommand(newCmd)
            response = "PRIVMSG "+self.bot.channel+" :"+response+"\n"
            sock.sendall(response.encode('utf-8'))
        elif command == "!resetcount":
            newCmd = " ".join(msg.msg.split()[1:])
            response = self.resetCustomCommandCount(newCmd)
            response = "PRIVMSG "+self.bot.channel+" :"+response+"\n"
            sock.sendall(response.encode('utf-8'))

        elif command == "!list":
            numCmds = 0
            cmds = []
            allCmds = []
            for cmd in self.bot.getRegCmds():
                allCmds.append(cmd[0])

            allCmds.sort()

            for cmd in allCmds:
                cmds.append(cmd)
                numCmds+=1
                if numCmds == 30: #30 commands per list message
                    cmdmsg = ", ".join(cmds)
                    sockMsg = "PRIVMSG "+self.bot.channel+" :"+cmdmsg+"\n"
                    sock.sendall(sockMsg.encode('utf-8'))
                    cmds = []
                    numCmds = 0

            if len(cmds) != 0:
                cmdmsg = ", ".join(cmds)
                sockMsg = "PRIVMSG "+self.bot.channel+" :"+cmdmsg+"\n"
                sock.sendall(sockMsg.encode('utf-8'))
                cmds = []
                numCmds = 0

            response = ", ".join(allCmds)


        else:
            if self.customCmds[command]:
                response = self.customCmds[command].getResponse(msg)
                response = "PRIVMSG "+self.bot.channel+" :"+response+"\n"
                sock.sendall(response.encode('utf-8'))

        #Now strip the IRC formatting off again so that we can log the response
        response = ":".join(response.split(":")[1:])
        response = response[:-1]

        #Export commands to update call counts
        self.exportCommands()

        return response

    def __init__(self,bot,name):
        super(CustomCmds,self).__init__(bot,name)
        self.modComLevel = REGULAR
        self.customCmds = {} #Dictionary of all custom commands implemented on this bot
        if not self.bot.isCmdRegistered("!addcom"):
            self.bot.regCmd("!addcom",self)
        else:
            print("!addcom is already registered to ",self.bot.getCmdOwner("!addcom"))

        if not self.bot.isCmdRegistered("!editcom"):
            self.bot.regCmd("!editcom",self)
        else:
            print("!editcom is already registered to ",self.bot.getCmdOwner("!editcom"))

        if not self.bot.isCmdRegistered("!delcom"):
            self.bot.regCmd("!delcom",self)
        else:
            print("!delcom is already registered to ",self.bot.getCmdOwner("!delcom"))

        if not self.bot.isCmdRegistered("!list"):
            self.bot.regCmd("!list",self)
        else:
            print("!list is already registered to ",self.bot.getCmdOwner("!list"))

        if not self.bot.isCmdRegistered("!resetcount"):
            self.bot.regCmd("!resetcount",self)
        else:
            print("!resetcount is already registered to ",self.bot.getCmdOwner("!resetcount"))

        self.importCommands()
