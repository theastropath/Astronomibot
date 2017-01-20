from astrolib.command import Command
from astrolib import MOD

import urllib
from urllib.request import urlopen
import os

configDir = "config"
apiFile = "CustomApi.txt"

class Api():
    def __init__(self,name,address):
        self.name = name
        self.address = address

    def getApiResponse(self):
        response = ""

        try:
            req = urllib.request.Request(self.address)
            reqResp = urlopen(req)
            response = reqResp.read().decode()
        except urllib.error.HTTPError as e:
            response = "[HTTP Error "+str(e.code)+"]"
        except:
            response = "Invalid API"

        return response 

class CustomApi(Command):

    def __init__(self,bot,name):
        super(CustomApi,self).__init__(bot,name)

        self.customApis = {}
        self.importApis()
        if not self.bot.isCmdRegistered("!customapi"):
            self.bot.regCmd("!customapi",self)
        else:
            print("!customapi is already registered to ",self.bot.getCmdOwner("!customapi"))


    def getDescription(self, full=False):
        if full:
            return "Add more functionality to Astronomibot by calling on external APIs to serve up more functionality.  An API call can be included in a custom command by using $CUSTOMAPI(<api name>) in the command, or silently call the api using $SILENTAPI(<api name>)"
        else:
            return "Extend Astronomibot using external APIs"


    def getState(self):
        tables = []

        cmds = []
        cmds.append(("Command","Description","Example"))
        cmds.append(("create","Creates a new API access string","!customapi create <api name> <api address>"))
        cmds.append(("delete","Deletes an API access string","!customapi delete <api name> <api address>"))

        apis = []
        apis.append(("API Name","API Address"))
        for api in self.customApis.keys():
            apis.append((self.customApis[api].name,self.customApis[api].address))

        tables.append(cmds)
        tables.append(apis)
   
        return tables

    def getParams(self):
        params = []
        return params

    def setParam(self, param, val):
        pass

    def createApi(self,apiName,apiAddress):
        response = "Creating API '"+apiName+"' Which will access '"+apiAddress+"'"

        self.customApis[apiName]=Api(apiName,apiAddress)

        return response

    def deleteApi(self,apiName):
        response = "Deleting API '"+apiName+"'"
        del self.customApis[apiName]
        return response

    def exportApis(self):
        apiStorageFile = configDir+os.sep+self.bot.channel[1:]+os.sep+apiFile
        with open(apiStorageFile,mode='w',encoding='utf-8') as f:
            for api in self.customApis.keys():
                f.write(self.customApis[api].name+" "+self.customApis[api].address+"\n")

    def importApis(self):
        apiStorageFile = configDir+os.sep+self.bot.channel[1:]+os.sep+apiFile
        with open(apiStorageFile,encoding='utf-8') as f:
            for line in f:
                api = line.strip()
                apiName = api.split()[0]
                apiAddress = api.split()[1]
                self.createApi(apiName,apiAddress)


    #Expecting "!customapi [create|delete] <api name> <api address>
    def shouldRespond(self, msg, userLevel):

        if msg.messageType == 'PRIVMSG' and len(msg.msg)!=0 and userLevel>=MOD:
            fullmsg = msg.msg.split()
            if fullmsg[0].lower()=='!customapi':
                if (len(fullmsg)==3 and fullmsg[1].lower()=='delete'):
                    return True
                elif (len(fullmsg)==4 and fullmsg[1].lower()=='create'):
                    return True

        return False

    def respond(self,msg,sock):
        fullmsg = msg.msg.split()

        action = fullmsg[1]
        apiName = fullmsg[2]
        apiAddress=""
        if action.lower()=='create':
            apiAddress = fullmsg[3]

        response = ""

        if action=="create":
            
            #Check to see if command has already been scheduled.
            if apiName in self.customApis.keys():
                response = "Command has already been scheduled"
            else:
                response = self.createApi(apiName,apiAddress)

        elif action == "delete":
                #Ensure the scheduled command has already been created
                if apiName not in self.customApis.keys():
                    response = "Command has not yet been scheduled"
                else:
                    response=self.deleteApi(apiName)

        self.exportApis()

        ircResponse = "PRIVMSG "+self.bot.channel+" : "+response+"\n"
        sock.sendall(ircResponse.encode('utf-8'))

        return response
