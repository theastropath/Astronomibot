import os
from astrolib.feature import Feature

class OutputConfig(Feature):
    def __init__(self,bot,name):
        super(OutputConfig, self).__init__(bot,name)
        self.configOutputFreq = 60
        self.outputTime = 1
        self.configExt = ".cfg"
        self.configDir = "config"

    def getParams(self):
        params = []
        params.append({'title':'ConfigUpdateFreq','desc':'How frequently the configs should be output (seconds)','val':self.configOutputFreq/2})

        return params

    def setParam(self, param, val):
        if param == 'ConfigUpdateFreq':
            self.configOutputFreq = float(val) * 2

    def outputConfig(self,obj):
        if not os.path.exists(self.configDir+os.sep+self.bot.channel[1:]):
            os.makedirs(self.configDir+os.sep+self.bot.channel[1:])
        if (len(obj.getParams())>0) and (obj.paramsChanged() or not os.path.isfile(os.path.join(self.configDir,self.bot.channel[1:],obj.name+self.configExt))):
            with open(os.path.join(self.configDir,self.bot.channel[1:],obj.name+self.configExt),'w') as f:
                for param in obj.getParams():
                    f.write(param['title']+" "+str(param['val'])+"\r\n")

    def handleFeature(self,sock):
        self.outputTime = self.outputTime - 1
        if self.outputTime == 0:
            self.outputTime = self.configOutputFreq
            #Output configuration
            for command in self.bot.getCommands():
                self.outputConfig(command)
            for feature in self.bot.getFeatures():
                self.outputConfig(feature)
