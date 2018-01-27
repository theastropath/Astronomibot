from astrolib.command import Command
from astrolib import MOD
import requests
import os
from urllib.parse import quote

configDir = "config"
apiFile = "CustomApi.txt"

class Api():
    def __init__(self,name,address):
        self.name = name
        self.address = address

    def getApiResponse(self,remainder):
        splitRemain = remainder.split()
        apiAddress = self.address
        response = ""

        for i in range(1,10):
            if "${"+str(i)+"}" in apiAddress:
                if i<=len(splitRemain):
                    apiAddress=apiAddress.replace("${"+str(i)+"}",quote(splitRemain[i-1]))
                else:
                    response = "[Not enough parameters provided]"
                    return response

        try:
            
            #Tacking on this set of headers gives us more freedom to use different apis
            hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                   'Accept-Encoding': 'none',
                   'Accept-Language': 'en-US,en;q=0.8',
                   'Connection': 'keep-alive'}
            r = requests.get(apiAddress,headers=hdr)
            r.raise_for_status()
            response = r.text
        except requests.exceptions.HTTPError as e:
            response = "[HTTP Error "+str(e.response.status_code)+"]"
        except:
            response = "[Invalid API]"

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
                f.write(self.customApis[api].name+" "+self.customApis[api].address+"\r\n")

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
            
            #Check to see if API has already been created.
            if apiName in self.customApis.keys():
                response = "API has already been created"
            else:
                response = self.createApi(apiName,apiAddress)

        elif action == "delete":
                #Ensure the API has already been created
                if apiName not in self.customApis.keys():
                    response = "API does not exist"
                else:
                    response=self.deleteApi(apiName)

        self.exportApis()

        ircResponse = "PRIVMSG "+self.bot.channel+" : "+response+"\n"
        sock.sendall(ircResponse.encode('utf-8'))

        return response
