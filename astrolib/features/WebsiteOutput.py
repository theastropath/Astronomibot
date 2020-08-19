from ftplib import FTP
import ftplib
import os
from datetime import datetime
import time
from html import escape
from astrolib.feature import Feature
import threading
from traceback import print_exc
from time import sleep
import socket
ftpCredFile = "ftpcreds.txt"

# string-like wrapper class that marks a string as html-safe
# If HtmlSafeStr objects are joined with normal strings (through +, %, join or
# format) the normal strings are escaped and a HtmlSafeStr object is returned.
# This is a bit overdone, implementing more methods than used here.
# This is more or less like Ruby on Rails does it.
class HtmlSafeStr:
    __slots__ = '__str',

    def __init__(self, str):
        self.__str = str

    def __str__(self):
        return self.__str

    def __repr__(self):
        return 'HtmlSafeStr(%r)' % self.__str

    def __add__(self, other):
        return HtmlSafeStr(self.__str + str(h(other)))

    def __radd__(self, other):
        return HtmlSafeStr(str(h(other)) + self.__str)

    def __mul__(self, count):
        if type(count) is not int:
            raise ValueError

        return HtmlSafeStr(self.__str * count)

    __rmul__ = __mul__

    def __eq__(self, other):
        return self.__str == str(h(other))

    def __ne__(self, other):
        return self.__str != str(h(other))

    def __lt__(self, other):
        return self.__str < str(h(other))

    def __gt__(self, other):
        return self.__str > str(h(other))

    def __le__(self, other):
        return self.__str <= str(h(other))

    def __ge__(self, other):
        return self.__str >= str(h(other))

    def __hash__(self):
        return hash(self.__str)

    def __mod__(self, args):
        if isinstance(args, str):
            return HtmlSafeStr(self.__str % str(h(args)))

        return HtmlSafeStr(self.__str % tuple(str(h(arg)) for arg in args))

    def __len__(self):
        return len(self.__str)

    def join(self, strs):
        return HtmlSafeStr(self.__str.join(str(h(s)) for s in strs))

    def format(self, *args, **kwargs):
        return HtmlSafeStr(self.__str.format(**dict((key, h(value)) for key, value in kwargs.items())))

# escape string, but only if needed and return marked as html-safe
def h(s):
    if isinstance(s, HtmlSafeStr):
        return s

    return HtmlSafeStr(escape(str(s)))

# very simple html template function
def templ(*args, **kwargs):
    templstr, args = args[0], args[1:]
    return HtmlSafeStr(templstr).format(*args, **kwargs)

class WebsiteOutput(Feature):
    def startHtmlFile(self,title,background="000000"):
        response = templ('''\
<!DOCTYPE html>
<html>
<head>
<style>
table, th, td {{ border: 1px solid black; }}
body {{ background: #{background} }}
</style>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta http-equiv="refresh" content="{refresh}" />
<title>{title}</title>
</head>
<body>
''', refresh=int(self.refreshFreq), title=title, background=background)
        return response

    def endHtmlFile(self):
        response = "</body></html>"
        return response

    def outputFile(self,file,name):
        if not os.path.exists(self.outputLocation+os.sep+self.bot.channel[1:]):
            os.makedirs(self.outputLocation+os.sep+self.bot.channel[1:])

        with open(self.outputLocation+os.sep+self.bot.channel[1:]+os.sep+name+".html",'w',encoding='utf-8') as f:
            f.write(file)

    def htmlLink(self,text,url):
        return templ('<a href="{url}">{text}</a>', url=url, text=text)

    def generateTablePage(self,tables,name,fullDescription="",filename=""):
        buf = [
            self.startHtmlFile(name, "DCDCDC"),
            templ("<h1>{name}</h1>", name=name),
            HtmlSafeStr('<br/>').join(fullDescription.split('\n')),
            '<br/><br/>'
        ]

        if filename != "index": #Kludge, yo
            buf.append(self.htmlLink("Return to Index", "index.html"))
            buf.append("<br/><br/>")

        for table in tables:
            if table:
                buf.append("<table><thead><tr>")

                #Column titles
                for element in table[0]:
                    buf.append(templ('<th>{hdr}</th>', hdr=element))

                buf.append("</tr></thead><tbody>")

                for row in table[1:]:
                    buf.append('<tr>')
                    for element in row:
                        buf.append(templ('<td>{cell}</td>', cell=element))
                    buf.append('</tr>')

                buf.append("</tbody></table><br/><br/>")

        buf.append(templ('<br/><small><i>Page generated at {time} {tz}</i></small>',
            time=datetime.now().ctime(),
            tz=time.tzname[time.localtime().tm_isdst]
        ))

        buf.append(self.endHtmlFile())
        page = ''.join(str(chunk) for chunk in buf)

        if not filename:
            filename = name
        self.outputFile(page, filename)

    def connectFtp(self):
        try:
            self.ftp = FTP(self.ftpUrl,self.ftpUser,self.ftpPass,timeout=30)
            self.ftp.set_pasv(True)
            self.ftp.cwd(self.ftpDir)
            print("FTP Connection Opened at "+datetime.now().ctime())
        except Exception as e:
            print("Couldn't connect to FTP ("+str(type(e))+") at "+datetime.now().ctime())


    def ftpUpload(self):
        try:
            self.ftp.voidcmd("NOOP")
        except:
            self.connectFtp()
        if os.path.exists(self.outputLocation+os.sep+self.bot.channel[1:]):
            #ftp = None
            try:
                for file in os.listdir(self.outputLocation+os.sep+self.bot.channel[1:]):
                    filepath = self.outputLocation+os.sep+self.bot.channel[1:]+os.sep+file
                    with open(filepath,'rb') as f:
                        self.ftp.storbinary("STOR "+file+".tmp",f)
                for file in self.ftp.nlst():
                    if ".tmp" in file:
                        self.ftp.rename(file,file[:-4])
            except socket.timeout as e:
                pass #I don't really care about a timeout, just reconnect plz
            except ftplib.all_errors as e:
                print("Encountered an error "+str(type(e))+" trying to deal with the FTP connection at "+datetime.now().ctime()+": "+str(e))
                print_exc()                
                if self.ftp is not None:
                    try:
                        self.ftp.quit()
                        print("FTP Connection gracefully closed at "+datetime.now().ctime())
                    except ftplib.all_errors as e:
                        print ("Encountered an error when trying to quit FTP connection: "+str(e))
                        print_exc()
                        self.ftp.close()
    def uploadTask(self):
        print("Upload Task Started")
        while(True):
            if self.startUpload:                   
                self.ftpUpload()
                self.startUpload = False

    def websiteGenerationTask(self):
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

        self.generateTablePage([[("User","User Level")]+self.bot.getChatters()],"Chatters","All users currently in the chat channel","chatters")
        indexTable.append((self.htmlLink("Chatters","chatters.html"),"A list of all users in chat"))

        self.generateTablePage([indexTable],"Astronomibot","","index")

        if self.ftpUrl!="":
            #This should probably be more threadsafe, but it's probably fine considering the low risk
            self.startUpload=True
            if not self.uploadThread.is_alive():
                self.uploadThread = threading.Thread(target=self.uploadTask)
                self.uploadThread.start()                    
            #uploadThread = threading.Thread(target=self.ftpUpload)
            #uploadThread.start()
            #print("Number of living threads after: "+str(threading.active_count()))
        
            
    def __init__(self,bot,name):
        super(WebsiteOutput,self).__init__(bot,name)
        self.htmlUpdateFreq = 120 #600 #In units based on the pollFreq (In astronomibot.py)
        self.htmlUpdate = 1
        self.outputLocation = "web"
        self.ftpUser=""
        self.ftpPass=""
        self.ftpUrl=""
        self.ftpDir=""
        self.startUpload = False
        self.refreshFreq=int((bot.pollFreq * self.htmlUpdateFreq)/2)

        self.ftpUrl =  self.bot.config["FTP"]["ftpurl"]
        self.ftpUser = self.bot.config["FTP"]["ftpuser"]
        self.ftpPass = self.bot.config["FTP"]["ftppassword"]
        self.ftpDir =  self.bot.config["FTP"]["ftpdir"]

        self.uploadThread = threading.Thread(target=self.uploadTask)
        self.uploadThread.start()

        self.websiteGenThread = None



    def handleFeature(self,sock):
        self.htmlUpdate = self.htmlUpdate - 1
        if self.htmlUpdate == 0:
            self.htmlUpdate = self.htmlUpdateFreq
            
            self.websiteGenThread = threading.Thread(target=self.websiteGenerationTask)
            self.websiteGenThread.start()                    
