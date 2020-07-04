import limitlessled
from limitlessled import Color
from limitlessled.bridge import Bridge
from limitlessled.group.rgbww import RGBWW
from limitlessled.presets import COLORLOOP
from limitlessled.group.commands.v6 import CommandV6

import webcolors
from astrolib.command import Command
from astrolib import BROADCASTER,NOTIF_CHANNELPOINTS
from time import sleep

class MiLight(Command):

    def __init__(self,bot,name):
        super(MiLight,self).__init__(bot,name)

        self.lightgroup=0
        self.lastState = "               "
        self.lightcontrollerip = ''
        self.lightcontrollerport = 8899
        self.enabled = False
        self.paramsHaveChanged = False
        self.groups=[]
        self.brightness=1.0
        self.lastColour=(255,255,255)

        self.bot.subToNotification(NOTIF_CHANNELPOINTS,self.channelPointHandler)

        if not self.bot.isCmdRegistered("!light"):
            self.bot.regCmd("!light",self)
        else:
            print("!light is already registered to ",self.bot.getCmdOwner("!light"))

        if not self.bot.isCmdRegistered("!lightgroup"):
            self.bot.regCmd("!lightgroup",self)
        else:
            print("!lightgroup is already registered to ",self.bot.getCmdOwner("!lightgroup"))

        #if not self.bot.isCmdRegistered("!disco"):
        #    self.bot.regCmd("!disco",self)
        #else:
        #    print("!disco is already registered to ",self.bot.getCmdOwner("!disco"))

        #if not self.bot.isCmdRegistered("!swirl"):
        #    self.bot.regCmd("!swirl",self)
        #else:
        #    print("!swirl is already registered to ",self.bot.getCmdOwner("!swirl"))

        if self.lightgroup!=0 and len(self.lightcontrollerip)>0:
            self.bridge = Bridge('192.168.1.39')
            self.groups=[]
            for groupnum in range(1,5):
                self.groups.append(self.bridge.add_group(groupnum,str(groupnum),RGBWW))
            
            self.enabled = True

    def channelPointHandler(self,data,sock):
        #print("Got: "+str(data))
        if data["reward"]=="White Lights":
            #print("Setting lights to white")
            self.groups[self.lightgroup-1].on = True
            self.groups[self.lightgroup-1].transition(brightness=1,temperature=0,duration=0)
            sleep(0.1)
            self.groups[self.lightgroup-1].transition(brightness=1,temperature=0,duration=0)
            self.lastColour=(255,255,255)
            self.lastState = "R255 G255 B255"
            
        elif data["reward"]=="Disco Lights":
            #print("Setting lights to disco mode")
            self.groups[self.lightgroup-1].on = True
            self.setPartyMode(5)
            sleep(0.1)
            self.setPartyMode(5)
            self.lastState="Disco Mode"
        elif data["reward"]=="Colour Swirl":
            #print("Setting lights to colour swirl")
            self.groups[self.lightgroup-1].on = True
            self.setPartyMode(2)
            sleep(0.1)
            self.setPartyMode(2)
            self.lastState="Rainbow Swirl Mode"

        return None
        
    def getState(self):
        tables = []

        state=[]
        state.append(("",""))
        state.append(("Last State",self.lastState))
        state.append(("Brightness %",self.brightness*100))
        state.append(("Light Group",str(self.lightgroup)))
        state.append(("",""))

        cmds = []
        cmds.append(("Command","Description","Example"))
        cmds.append(("!light <r> <g> <b>","Specify an exact colour with RGB values for the light.  Values are between 0 and 255","!light 255 0 128"))
        cmds.append(("!light <Colour name>","Set a light colour by name.  Accepts HTML colour names.","!light olivegreen"))
        cmds.append(("!brightness","Sets the light brightness, in percent","!brightness 75"))
        #cmds.append(("!disco","Makes the light flash between various colours","!disco"))
        #cmds.append(("!swirl","Makes the light gently swirl between all the colours","!swirl"))


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
        changed = False
        if param == 'LightGroup':
            if self.lightgroup!=int(val):
                changed=True
            self.lightgroup = int(val)
        if param == 'LightControllerIP':
            if self.lightcontrollerip!=val:
                changed=True
            self.lightcontrollerip = val
        if param == 'LightControllerPort':
            if self.lightcontrollerport!=int(val):
                changed=True
            self.lightcontrollerport = int(val)

        if self.lightgroup!=0 and len(self.lightcontrollerip)>0:
            if changed:
                #print("Setting params milight")
                self.bridge = Bridge(self.lightcontrollerip)
                self.groups=[]
                for groupnum in range(1,5):
                    self.groups.append(self.bridge.add_group(groupnum,str(groupnum),RGBWW))

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
            if splitMsg[0]=='!light' and len(splitMsg)==2:
                try:
                    webcolors.name_to_rgb(splitMsg[1])
                    return True
                except:
                    return False
            if splitMsg[0]=='!disco':
                return False
            if splitMsg[0]=='!swirl':
                return False
            if splitMsg[0]=='!lightgroup' and userLevel == BROADCASTER:
                return True
            if splitMsg[0]=='!brightness' and len(splitMsg)==2:
                if splitMsg[1].isdigit():
                    return True
        return False

    def setPartyMode(self,mode):
        #LimitlessLED package does not yet support party modes.  Manual implementation...
        message = [0x80,0x00,0x00,0x00,0x11,int(self.bridge._wb1),int(self.bridge._wb2),0x00,int(self.bridge._sn),0x00]
        partyCommand = [0x31,0x00,0x00,0x08,0x06,int(mode),0x00,0x00,0x00,int(self.lightgroup),0x00]
        checksum = 0
        for val in partyCommand:
            checksum += int(val)
        checksum = checksum & 0xFF
        partyCommand.append(checksum)
        message = message + partyCommand
        #print(str(message))
        self.bridge._send_raw(message)
        sleep(0.1)
        self.bridge._send_raw(message) #Send twice as sometimes it doesn't actually happen


    def respond(self,msg,sock):
        splitMsg = msg.msg.split()
        response=""

        if splitMsg[0]=='!light':
            if len(splitMsg)==2:
                colour=webcolors.name_to_rgb(splitMsg[1])
                red = colour[0]
                green = colour[1]
                blue = colour[2]

            else:
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
                    
            fullWhite = False

            if red==255 and green==255 and blue==255:
                fullWhite = True

            #self.cont.send(self.light.color(milight.color_from_rgb(red,green,blue),self.lightgroup))
            if fullWhite:
                self.groups[self.lightgroup-1].on = True
                self.groups[self.lightgroup-1].transition(brightness=self.brightness,duration=0,temperature=0)
                sleep(0.1)
                self.groups[self.lightgroup-1].transition(brightness=self.brightness,duration=0,temperature=0)
                
            elif red or green or blue:
                self.groups[self.lightgroup-1].on = True
                self.groups[self.lightgroup-1].transition(brightness=self.brightness,duration=0,color=Color(red,green,blue))
                sleep(0.1)
                self.groups[self.lightgroup-1].transition(brightness=self.brightness,duration=0,color=Color(red,green,blue))

            else:
                self.groups[self.lightgroup-1].on = False

            self.lastColour=(red,green,blue)
            self.lastState = "R"+str(red)+" G"+str(green)+" B"+str(blue)
            response = "Light changed to R"+str(red)+" G"+str(green)+" B"+str(blue)

        elif splitMsg[0]=='!disco':
            self.groups[self.lightgroup-1].on = True
            self.setPartyMode(5)
            self.lastState="Disco Mode"
            response = "Light switched to disco mode"

        elif splitMsg[0]=='!swirl':
            self.groups[self.lightgroup-1].on = True

            self.setPartyMode(2)
            self.lastState="Rainbow Swirl Mode"
            response = "Light switched to rainbow swirl mode"

        elif splitMsg[0]=='!brightness':
            newBrightness=int(splitMsg[1])
            if newBrightness<0:
                newBrightness=0
            elif newBrightness>100:
                newBrightness=100

            self.brightness=newBrightness/100.0
            if self.lastColour[0] or self.lastColour[1] or self.lastColour[2]:
                self.groups[self.lightgroup-1].on = True
                self.groups[self.lightgroup-1].transition(brightness=self.brightness,duration=0,color=Color(self.lastColour[0],self.lastColour[1],self.lastColour[2]))
                sleep(0.1)
                self.groups[self.lightgroup-1].transition(brightness=self.brightness,duration=0,color=Color(self.lastColour[0],self.lastColour[1],self.lastColour[2]))                
            else:
                self.groups[self.lightgroup-1].on = False
                
            response = "Light brightness set to "+str(newBrightness)+"%"



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
