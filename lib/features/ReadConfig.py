import os
from ..feature import Feature

class ReadConfig(Feature):
    def __init__(self,bot,name):
        super(ReadConfig, self).__init__(bot,name)
        self.configReadFreq = 60
        self.readTime = 1
        self.configExt = ".cfg"
        self.configDir = "config"

    def getParams(self):
        params = []
        params.append({'title':'ConfigReadFreq','desc':'How frequently the configs should be read (seconds)','val':self.configReadFreq/2})

        return params

    def setParam(self, param, val):
        if param == 'ConfigReadFreq':
            self.configReadFreq = float(val) * 2

    def readConfig(self,obj):
        if os.path.exists(self.configDir+os.sep+self.bot.channel[1:]):
            if len(obj.getParams())>0: #Has parameters to configure
                try:
                    with open(os.path.join(self.configDir,self.bot.channel[1:],obj.name+self.configExt),'r') as f:
                        for line in f:
                            param, val = line.strip().split(None, 1)
                            obj.setParam(param, val)
                except FileNotFoundError:
                    pass

    def handleFeature(self,sock):
        self.readTime = self.readTime - 1
        if self.readTime == 0:
            self.readTime = self.configReadFreq
            #Output configuration
            for command in self.bot.getCommands():
                self.readConfig(command)
            for feature in self.bot.getFeatures():
                self.readConfig(feature)
