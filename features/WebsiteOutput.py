import imp
from ftplib import FTP
import os
from datetime import datetime
import time

baseFile = "astronomibot.py"
if __name__ == "__main__":
    baseFile = "../"+baseFile
    
c = imp.load_source('Command',baseFile)

ftpCredFile = "ftpcreds.txt"

class WebsiteOutput(c.Feature):
    htmlUpdateFreq = 120 #600 #In units based on the pollFreq (In astronomibot.py)
    htmlUpdate = 1
    outputLocation = "web"
    ftpUser=""
    ftpPass=""
    ftpUrl=""
    ftpDir=""

    def startHtmlFile(self,title,background="000000"):
        response = '<!DOCTYPE html><html><head>'
        response+= '<style>table, th, td { border: 1px solid black; }</style>'
        response+= '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'
        response+= '<title>'+str(title)+'</title>'
        response+= '</head><body bgcolor="#'+background+'">'
        return response

    def endHtmlFile(self):
        response = "</body></html>"
        return response

    def outputFile(self,file,name):
        if not os.path.exists(self.outputLocation+os.sep+self.bot.channel[1:]):
            os.makedirs(self.outputLocation+os.sep+self.bot.channel[1:])

        f = open(self.outputLocation+os.sep+self.bot.channel[1:]+os.sep+name+".html",'w',encoding='utf-8')
        f.write(file)
        f.close()

    def htmlLink(self,text,url):
        return '<a href="'+url+'">'+text+'</a>'

    def generateTablePage(self,tables,name,fullDescription="",filename=""):
        page = ""
        page += self.startHtmlFile(name,"DCDCDC")
        page += "<h1>"+name+"</h1>"

        page+=fullDescription.replace('\n','<br>')+"<br><br>"
    
        if filename != "index": #Kludge, yo
            page += self.htmlLink("Return to Index","index.html")+"<br><br>"
        for table in tables:
            if len(table)>0:
                page +="<table>"

                #Column titles
                page  += "<tr>"
                for element in table[0]:
                    page +="<td>"
                    page +="<b>"+element+"</b>"
                    page +="</td>"
                page  += "</tr>"
                for row in table[1:]:
                    page +="<tr>"
                    for element in row:
                        page+="<td>"
                        page+=str(element)
                        page+="</td>"
                    page +="</tr>"
                page +="</table>"
                page+="<br><br>"
        page += "<br><small><i>Page generated at "+datetime.now().ctime()+" "+time.tzname[time.localtime().tm_isdst]+"</i></small>"
        
        page += self.endHtmlFile()
        if filename == "":
            filename = name
        self.outputFile(page,filename)

    def ftpUpload(self):
        if os.path.exists(self.outputLocation+os.sep+self.bot.channel[1:]):
            try:
                ftp = FTP(self.ftpUrl,self.ftpUser,self.ftpPass)
                ftp.cwd(self.ftpDir)
                for file in os.listdir(self.outputLocation+os.sep+self.bot.channel[1:]):
                    filepath = self.outputLocation+os.sep+self.bot.channel[1:]+os.sep+file
                    f = open(filepath,'rb')
                    ftp.storlines("STOR "+file,f)
                ftp.close()
            except:
                print("Encountered an error trying to deal with the FTP connection")
                ftp.close()
            
    def __init__(self,bot,name):
        super(WebsiteOutput,self).__init__(bot,name)
        try:
            f = open(ftpCredFile)
            self.ftpUrl = f.readline().strip('\n')
            self.ftpUser = f.readline().strip('\n')
            self.ftpPass = f.readline().strip('\n')
            self.ftpDir = f.readline().strip('\n')
        except FileNotFoundError:
            pass #No FTP cred file found.  Just won't try to upload.
        
        
    def handleFeature(self,sock):
        self.htmlUpdate = self.htmlUpdate - 1
        if self.htmlUpdate == 0:
            self.htmlUpdate = self.htmlUpdateFreq
            
            indexMods = []
            indexTable = [("Module Name","Description")]
            for cmd in self.bot.getCommands():
                state = cmd.getState()
                if state != None:
                    indexMods.append(cmd)
                    self.generateTablePage(state,cmd.name,cmd.getDescription(True))

            for ftr in self.bot.getFeatures():
                state = ftr.getState()
                if state != None:
                    indexMods.append(ftr)
                    self.generateTablePage(state,ftr.name,ftr.getDescription(True))

            for mod in indexMods:
                indexTable.append((self.htmlLink(mod.name,mod.name+".html"),mod.getDescription()))

            self.generateTablePage([[("<b>User</b>","<b>User Level</b>")]+self.bot.getChatters()],"Chatters","All users currently in the chat channel","chatters")
            indexTable.append((self.htmlLink("Chatters","chatters.html"),"A list of all users in chat"))
  
            self.generateTablePage([indexTable],"Astronomibot","","index")

            if self.ftpUrl!="":
                self.ftpUpload()
        
