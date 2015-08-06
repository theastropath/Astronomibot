import imp
baseFile = "astronomibot.py"
if __name__ == "__main__":
    baseFile = "../"+baseFile
    
c = imp.load_source('Command',baseFile)

class Ping(c.Command):
    def shouldRespond(self, msg, userLevel):
        return msg.messageType=="PING"

    def respond(self,msg,sock):
        print ("Responding to PING")
        sock.sendall(b"PONG "+msg.msg.encode('utf-8')+b"\n")
        return ""
        
