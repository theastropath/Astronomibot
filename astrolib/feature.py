#############################################################################################################
# This class defines the API for interacting with "features"
# Implementations of this class must be made in an individual .py file in the
# lib/feature folder, and the implemented class must have the same name as the file
#############################################################################################################

class Feature:

    #This function will go off and do whatever this feature is supposed to do
    def handleFeature(self,sock):
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
        return "A generic undescribed Feature"

    #Equals is used for checking if the name is in the feature list
    def __eq__(self,key):
        return key == self.name

    def __init__(self,bot,name):
        self.name = name
        self.bot = bot
