import imp
import os
baseFile = "astronomibot.py"
if __name__ == "__main__":
    baseFile = "../"+baseFile
    
c = imp.load_source('Command',baseFile)

class OutputConfig(c.Command):
    configOutputFreq = 60
    outputTime = 1
    configExt = ".cfg"
    configDir = "config"

    def outputConfig(self,command):
        if not os.path.exists(self.configDir+os.sep+self.bot.channel[1:]):
            os.makedirs(self.configDir+os.sep+self.bot.channel[1:])
        if len(command.getParams())>0:
            f = open(os.path.join(self.configDir,self.bot.channel[1:],command.name+self.configExt),'w')
            for param in command.getParams():
                f.write(param['title']+" "+str(param['val'])+"\n")
            f.close()
    
    def handleFeature(self,sock):
        self.outputTime = self.outputTime - 1
        if self.outputTime == 0:
            self.outputTime = self.configOutputFreq
            #Output configuration
            for command in self.bot.getCommands():
                self.outputConfig(command)

                    
        
