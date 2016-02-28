import imp
baseFile = "astronomibot.py"
if __name__ == "__main__":
    baseFile = "../"+baseFile
    
c = imp.load_source('Command',baseFile)

class TestFeature(c.Command):

    def handleFeature(self,sock):
        pass
        #print("Test feature!")
        
