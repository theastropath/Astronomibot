#############################################################################################################
# This class defines the API for interacting with "commands"
# Implementations of this class must be made in an individual .py file in the lib/command
# folder, and the implemented class must have the same name as the file
#############################################################################################################

class Command:

    #This function will take a msg and respond if this "command" should respond (True or False)
    def shouldRespond(self, msg, userLevel):
        raise NotImplementedError()

    #This function will actually respond to the message
    def respond(self,msg,sock):
        raise NotImplementedError()

    def getParams(self):
        params = []
        return params

    def setParam(self, param, val):
        pass

    def paramsChanged(self):
        return False

    def getState(self):
        return None

    def getDescription(self,full=False):
        return "A generic undescribed Command"

    def htmlInDesc(self):
        return False

    #Equals is used for checking if the name is in the command list
    def __eq__(self,key):
        return key == self.name

    def __init__(self,bot,name):
        self.name = name
        self.bot = bot
