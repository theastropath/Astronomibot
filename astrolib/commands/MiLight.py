import milight
import webcolors
from astrolib.command import Command
from astrolib import BROADCASTER

class MiLight(Command):

    def __init__(self,bot,name):
        super(MiLight,self).__init__(bot,name)

        self.lightgroup=0
        self.lastState = "               "
        self.lightcontrollerip = ''
        self.lightcontrollerport = 8899
        self.enabled = False
        self.paramsHaveChanged = False

        if not self.bot.isCmdRegistered("!light"):
            self.bot.regCmd("!light",self)
        else:
            print("!light is already registered to ",self.bot.getCmdOwner("!light"))

        if not self.bot.isCmdRegistered("!lightgroup"):
            self.bot.regCmd("!lightgroup",self)
        else:
            print("!lightgroup is already registered to ",self.bot.getCmdOwner("!lightgroup"))

        if not self.bot.isCmdRegistered("!disco"):
            self.bot.regCmd("!disco",self)
        else:
            print("!disco is already registered to ",self.bot.getCmdOwner("!disco"))

        if not self.bot.isCmdRegistered("!swirl"):
            self.bot.regCmd("!swirl",self)
        else:
            print("!swirl is already registered to ",self.bot.getCmdOwner("!swirl"))

        if self.lightgroup!=0 and len(self.lightcontrollerip)>0:
            self.cont = milight.MiLight({'host':self.lightcontrollerip,'port':self.lightcontrollerport},wait_duration=0)
            self.light = milight.LightBulb(['rgbw'])
            self.cont.send(self.light.on(self.lightgroup))
            self.enabled = True

    def getState(self):
        tables = []

        state=[]
        state.append(("",""))
        state.append(("Last State",self.lastState))
        state.append(("Light Group",str(self.lightgroup)))
        state.append(("",""))

        cmds = []
        cmds.append(("Command","Description","Example"))
        cmds.append(("!light <r> <g> <b>","Specify an exact colour with RGB values for the light.  Values are between 0 and 255","!light 255 0 128"))
        cmds.append(("!disco","Makes the light flash between various colours","!disco"))
        cmds.append(("!swirl","Makes the light gently swirl between all the colours","!swirl"))

        tables.append(state)
        tables.append(cmds)

        return tables

    def getDescription(self, full=False):
        if full:
            return "Users can use various commands to mess with an RGB light in the room!  Uses cheap MiLight light bulbs."
        else:
            return "Control an RGB light bulb!"


    def getParams(self):
        params = [{'title':'LightGroup','desc':'Which MiLight light group to control','val':self.lightgroup}]
        params.append({'title':'LightControllerIP','desc':'IP of MiLight Wifi controller','val':self.lightcontrollerip})
        params.append({'title':'LightControllerPort','desc':'UDP Port of MiLight Wifi controller','val':self.lightcontrollerport})

        return params

    def setParam(self, param, val):
        if param == 'LightGroup':
            self.lightgroup = int(val)
        if param == 'LightControllerIP':
            self.lightcontrollerip = val
        if param == 'LightControllerPort':
            self.lightcontrollerport = int(val)

        if self.lightgroup!=0 and len(self.lightcontrollerip)>0:
            self.cont = milight.MiLight({'host':self.lightcontrollerip,'port':self.lightcontrollerport},wait_duration=0)
            self.light = milight.LightBulb(['rgbw'])
            self.enabled = True
        else:
            self.enabled = False

        self.paramsHaveChanged = False

    def paramsChanged(self):
        return self.paramsHaveChanged

    def shouldRespond(self, msg, userLevel):
        if not self.enabled:
            return False
        if self.lightgroup==0 or len(self.lightcontrollerip)==0:
            return False
        if msg.messageType == 'PRIVMSG' and len(msg.msg)!=0:
            splitMsg = msg.msg.split()
            if splitMsg[0]=='!light' and len(splitMsg)==4:
                if splitMsg[1].isdigit() and splitMsg[2].isdigit() and splitMsg[3].isdigit():
                    return True
            if splitMsg[0]=='!disco':
                return True
            if splitMsg[0]=='!swirl':
                return True
            if splitMsg[0]=='!lightgroup' and userLevel == BROADCASTER:
                return True
        return False


    def respond(self,msg,sock):
        splitMsg = msg.msg.split()
        response=""

        if splitMsg[0]=='!light':
            red = int(splitMsg[1])
            if red<0:
                red=0
            elif red>255:
                red=255

            green = int(splitMsg[2])
            if green<0:
                green=0
            elif green>255:
                green=255

            blue = int(splitMsg[3])
            if blue<0:
                blue=0
            elif blue>255:
                blue=255

            self.cont.send(self.light.color(milight.color_from_rgb(red,green,blue),self.lightgroup))
            self.lastState = "R"+str(red)+" G"+str(green)+" B"+str(blue)
            response = "Light changed to R"+str(red)+" G"+str(green)+" B"+str(blue)

        elif splitMsg[0]=='!disco':
            self.cont.send(self.light.party('rainbow_jump',self.lightgroup))
            self.lastState="Disco Mode"
            response = "Light switched to disco mode"

        elif splitMsg[0]=='!swirl':
            self.cont.send(self.light.party('rainbow_swirl',self.lightgroup))
            self.lastState="Rainbow Swirl Mode"
            response = "Light switched to rainbow swirl mode"

        elif splitMsg[0]=='!lightgroup':
            if len(splitMsg)>1:
                if splitMsg[1].isdigit():
                    group = int(splitMsg[1])
                    if group>=1 and group <=4:
                        self.lightgroup=group
                        self.paramsHaveChanged = True
                        response = "Switched to MiLight light group "+str(group)
                    else:
                        response = "Invalid MiLight light group"
                else:
                    response = "Invalid MiLight light group"
            else:
                response = "No MiLight light group provided"

        ircResponse = "PRIVMSG "+self.bot.channel+" :"+response+"\n"
        sock.sendall(ircResponse.encode('utf-8'))
        return response
