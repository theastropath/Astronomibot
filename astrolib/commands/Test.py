from astrolib.command import Command

class Test(Command):

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
