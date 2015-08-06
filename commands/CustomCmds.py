import imp
baseFile = "astronomibot.py"
if __name__ == "__main__":
    baseFile = "../"+baseFile
c = imp.load_source('Command',baseFile)

customCmds = {} #Dictionary of all custom commands implemented on this bot
cmdFile = "cmds.txt"

class CustomCommand:
    command = ""
    response = ""
    userlevel = EVERYONE

    def __init__(self,command,response,userlevel=EVERYONE):
        self.command = command
        self.response = response
        self.userlevel=userlevel

    def canUseCommand(self,userlevel):
        return userlevel>=self.userlevel

    def getResponse(self,msg):
        afterCmd = " ".join(msg.msg.split()[1:]).rstrip()
        if len(afterCmd)>0 and afterCmd[0]=="/":
            afterCmd = ""
        return self.response.replace(replaceTerm,afterCmd)

    def exportCommand(self):
        return self.command+" "+str(self.userlevel)+" "+self.response+'\n'

def exportCommands():
    commands = channel[1:]+cmdFile
    f = open(commands,mode='w',encoding="utf-8")
    for cmd in customCmds.keys():
        f.write(customCmds[cmd].exportCommand())
    f.close()
    
def importCommands():
    commands = channel[1:]+cmdFile
    try:
        f = open(commands,encoding="utf-8")
        for line in f:
            command = line.split()[0].lower()
            userLvl = int(line.split()[1])
            response = " ".join(line.split()[2:]).rstrip()
            customCmds[command]=CustomCommand(command,response,userLvl)
        f.close()
    except FileNotFoundError:
        print (commands+" is not present, no commands imported")

def addCustomCommand(command):
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
        elif newCmd == "EVERYONE":
            newCmd = command.split()[1]
            cmdResp = " ".join(command.split()[2:])
            userLevel=EVERYONE
        else:
            return "Invalid user level for command!"

    if cmdResp[0]=="/" or cmdResp[0]==".":
        return "Tut tut, don't try that!"

    newCmd = newCmd.lower()

    if newCmd in customCmds.keys():
        return "Command '"+newCmd+"' already exists!"
    elif len(newCmd)==1:
        return "No command name given!"
    else:
        customCmds[newCmd]=CustomCommand(newCmd,cmdResp,userLevel)
        exportCommands()
        return "Adding "+newCmd+" which will respond with '"+cmdResp+"'"

def editCustomCommand(command):
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

    if newCmd in customCmds.keys():
        customCmds[newCmd].response = cmdResp
        if userLevelChanged:
            customCmds[newCmd].userlevel = userLevel
        exportCommands()
        return "Editing "+newCmd+" which will now respond with '"+cmdResp+"'"    
    elif len(newCmd)==1:
        return "No command name given!"
    else:
        return "Command '"+newCmd+"' doesn't exist!"

def delCustomCommand(command):
    cmd = command.split()[0]

    if cmd[0]=="!":
        if cmd in customCmds.keys():
            del customCmds[cmd]
            exportCommands()
            return "Command "+cmd+" has been deleted"
        else:
            return "Command "+cmd+" is not present"
            
    else:
        return  "No command name given!"


class CustomCmds(c.Command):
    def shouldRespond(self, msg, userLevel):
        if msg.messageType == 'PRIVMSG' and len(msg.msg)!=0:
            if msg.msg[0]=='!':
                command = msg.msg.split()[0].lower() #Only care about the first word
                #Only a few hardcoded commands, then user editable commands
                if command == "!addcom" or command == "!editcom" or command == "!delcom":
                    if userLevel>=EVERYONE:
                        return True
                elif command == "!list":
                    return True
                else:
                    if command in customCmds.keys():
                        if customCmds[command].canUseCommand(userLevel):
                            return True
               
        return False

    def respond(self,msg,sock):
        command = msg.msg.split()[0].lower()
        response = ":"
        if command == "!addcom":
            newCmd = " ".join(msg.msg.split()[1:])
            response = addCustomCommand(newCmd)
            response = "PRIVMSG "+channel+" :"+response+"\n"
            sock.sendall(response.encode('utf-8'))
        elif command == "!editcom":
            newCmd = " ".join(msg.msg.split()[1:])
            response = editCustomCommand(newCmd)
            response = "PRIVMSG "+channel+" :"+response+"\n"
            sock.sendall(response.encode('utf-8'))
        elif command == "!delcom":
            newCmd = " ".join(msg.msg.split()[1:])
            response = delCustomCommand(newCmd)
            response = "PRIVMSG "+channel+" :"+response+"\n"
            sock.sendall(response.encode('utf-8'))
        elif command == "!list":
            response = ", ".join(customCmds.keys())
            response = "PRIVMSG "+channel+" :"+response+"\n"
            sock.sendall(response.encode('utf-8'))

        else:
            if customCmds[command]:
                response = customCmds[command].getResponse(msg)
                response = "PRIVMSG "+channel+" :"+response+"\n"
                sock.sendall(response.encode('utf-8'))

        #Now strip the IRC formatting off again so that we can log the response
        response = ":".join(response.split(":")[1:])
        response = response[:-1]
        return response

    def __init__(self,name):
        super(CustomCmds,self).__init__(name)
        importCommands()

