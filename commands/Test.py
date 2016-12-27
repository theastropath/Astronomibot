import imp
baseFile = "astronomibot.py"
if __name__ == "__main__":
    baseFile = "../"+baseFile
    
c = imp.load_source('Command',baseFile)

class Test(c.Command):

    def getParams(self):
        params = []
        return params

    def setParam(self, param, val):
        pass
    
    def shouldRespond(self, msg, userLevel):
        #print ("Test: Should we respond to message type "+msg.messageType+"?")
        return True

    def respond(self,msg,sock):
        #print ("Test: Responding")
        return ""
        
