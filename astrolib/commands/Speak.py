from astrolib.command import Command
import os
import markovify
from queue import Queue
import threading

class Speak(Command):

    def learningTask(self):
        while True:
            learnline = self.learningQueue.get(block=True)
            if self.isValidToLearn(learnline[0],learnline[1]):
                self.learnLine(learnline[0],learnline[1])
        
    
    def __init__(self,bot,name):
        super(Speak,self).__init__(bot,name)
        self.models = dict()
        self.learningQueue = Queue()
        self.learnedLines = 0
        
        self.learningThread = threading.Thread(target=self.learningTask)
        self.learningThread.start()
        
        self.learnFromLogs(25000)
        
        if not self.bot.isCmdRegistered("!speak"):
            self.bot.regCmd("!speak",self)
        else:
            print("!speak is already registered to ",self.bot.getCmdOwner("!speak"))

    def isValidToLearn(self,author,text):
        if author==self.bot.name: #Don't learn messages from the bot
            return False

        if text.startswith("!"): #Don't learn messages that are commands for the bot
            return False

        if text.startswith("/"): #Don't learn slash-messages (/me, /host, /ban, etc), just in case
            return False

        return True
    
    def learnFromLogs(self,linesToLearn):
        logDir = "."+os.sep+"logs"+os.sep+self.bot.channelName
        fileList = os.listdir(logDir)
        fileList.sort(reverse=True)


        for file in fileList:
            with open(logDir+os.sep+file,encoding='utf-8') as f:
                for line in f:
                    #print(line)
                    #Split the message into the author and the text
                    try:
                        splitLine = line.split(" ",3)
                        author,text = splitLine[3].split(": ",1)
                        text = text.strip()
                        #print(author)
                        #print(text)
                        #if self.learnLine(author.lower(),text):
                        #    linesLearned+=1

                        if self.isValidToLearn(author,text):
                            self.learningQueue.put((author,text))
                            self.learnedLines+=1

                        if self.learnedLines >= linesToLearn:
                            break
                    except:
                        print("Something went wrong trying to load lines into the Speak module")
            if self.learnedLines>=linesToLearn:
                break
        
    def learnLine(self,author,text):
        #print("Learning new line from "+author)
        if not self.isValidToLearn(author,text):
            return False #Don't learn our own messages
        try:
            #print("Building new model")
            newModel = markovify.Text(text,well_formed=False)
            if author in self.models:
                #print("Fetching old model")
                oldModel = self.models[author]
                #print("Combining models")
                combined = markovify.combine([oldModel,newModel])
                #print("Done")
                self.models[author] = combined
            else:
                self.models[author] = newModel
            return True
        except Exception as e:
            print(str(type(e))+" "+str(e))
            print(author+": "+text)

        return False

    def getCombinedModel(self):
        modelList = []
        for model in self.models.values():
            modelList.append(model)

        combinedModel = markovify.combine(modelList)

        return combinedModel
        
    def getParams(self):
        params = []
        return params

    def setParam(self, param, val):
        pass
    
    def getDescription(self, full=False):
        if full:
            return "Generates semi-reasonable sentences based off of things that you have said in chat!"
        else:
            return "Generates silly sentences based off of chat!"

    def getState(self):
        tables = []

        cmds = [
            ("Command","Description","Example"),
            ("!speak","Generates a sentence based on messages sent in chat by anybody","!speak"),
            ("!speak <user>","Generates a sentence based on the messages of the specified user","!speak theastropath")
        ]
        
        state=[]
        state.append(("",""))
        state.append(("Learned Lines of Text",self.learnedLines))
        state.append(("",""))
        
        tables.append(cmds)
        tables.append(state)

        return tables

    def shouldRespond(self, msg, userLevel):
        if msg.messageType == "PRIVMSG":
            if self.isValidToLearn(msg.sender,msg.msg):
                self.learningQueue.put((msg.sender,msg.msg))
                self.learnedLines+=1

            if len(msg.msg)!=0:
                splitmsg = msg.msg.split()
                if splitmsg[0].lower()=="!speak":
                    return True
        return False

    def respond(self,msg,sock):
        #This has to be a !speak command
        
        target = None
        textResponse = ""
        model = None

        splitmsg = msg.msg.split()

        if len(splitmsg)>1:
            target = splitmsg[1].lower()
        
        if target:
            if target in self.models:
                model = self.models[target]
        else:
            model = self.getCombinedModel()

        if model:
            #textResponse = model.make_sentence(test_output=False)
            textResponse = model.make_sentence(tries=250,max_overlap_ratio=0.99,max_overlap_total=25)
            if not textResponse:
                textResponse = "I couldn't think of anything interesting to say..."
        else:
            textResponse = "I don't know how to speak like "+target
        
        response = "PRIVMSG "+self.bot.channel+" : "+textResponse+"\n"
        sock.sendall(response.encode('utf-8'))

        return textResponse
