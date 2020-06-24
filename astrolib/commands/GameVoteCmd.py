from astrolib.command import Command
from requests import Session
import json
import os

configDir="config"
gamevoteCredFile = "gamevotecreds.txt"

class GameVoteCmd(Command):

    def __init__(self,bot,name):
        super(GameVoteCmd,self).__init__(bot,name)

        self.credsAvailable = False

        try:
            with open(gamevoteCredFile) as f:
                self.apiKey = f.readline().strip("\n")
                self.sheetId = f.readline().strip("\n")
                self.gameSheetName = f.readline().strip("\n")
                self.gameColumn = f.readline().strip("\n")
                self.statusColumn = f.readline().strip("\n")
                self.firstGameRow = int(f.readline().strip("\n"))
                self.randoSheetName = f.readline().strip("\n")
                self.randoGameColumn = f.readline().strip("\n")
                self.randoStatusColumn = f.readline().strip("\n")
                self.firstRandoRow = int(f.readline().strip("\n"))
                self.credsAvailable = True
        except:
            pass
                
        #Generated values
        if self.credsAvailable:
            self.fullGameRange = self.gameSheetName+"!"+self.gameColumn+str(self.firstGameRow)+":"+self.statusColumn+"1000"
            self.fullRandoRange = self.randoSheetName+"!"+self.randoGameColumn+str(self.firstRandoRow)+":"+self.randoStatusColumn+"1000"
            self.gameUrl = "https://sheets.googleapis.com/v4/spreadsheets/"+self.sheetId+"/values/"+self.fullGameRange+"?key="+self.apiKey
            self.randoUrl = "https://sheets.googleapis.com/v4/spreadsheets/"+self.sheetId+"/values/"+self.fullRandoRange+"?key="+self.apiKey
        else:
            self.gameUrl = ""
            self.randoUrl = ""
        
        self.voteFile = "votes.txt"

        self.gamevotes=[]
        self.randovotes=[]
        self.clearedgamevotes=[]
        self.clearedrandovotes=[]

        self.loadVotes()
        
        if not self.bot.isCmdRegistered("!schedulemsg"):
            self.bot.regCmd("!gamevote",self)
        else:
            print("!gamevote is already registered to ",self.bot.getCmdOwner("!gamevote"))
            
        if not self.bot.isCmdRegistered("!randovote"):
            self.bot.regCmd("!randovote",self)
        else:
            print("!randovote is already registered to ",self.bot.getCmdOwner("!randovote"))

    def getDescription(self,full=False):
        if full and self.credsAvailable:
            return 'Let viewers vote for games and randomizers.  The list of games can be found here: https://docs.google.com/spreadsheets/d/'+self.sheetId
        else:
            return "Let viewers vote for games"

    def getState(self):
        tables = []
        commands = []
        gamevotes = []
        randovotes = []

        commands.append(("Command Name","Description"))
        commands.append(("!gamevote","Show your current game vote"))
        commands.append(("!gamevote [game]","Vote for the first game in the spreadsheet that matches [game]"))
        commands.append(("!randovote","Show your current randomizer vote"))
        commands.append(("!randovote [game]","Vote for the first randomizer in the spreadsheet that matches [game]"))

        gamevotes.append(("Game Name","Number of Votes"))
        gamevotecounts = []
        for gamevote in self.gamevotes:
            found = False
            for count in gamevotecounts:
                if count[0] == gamevote[1]:
                    count[1] = count[1]+1
                    found = True
            if not found:
                gamevotecounts.append([gamevote[1],1])

        gamevotecounts = sorted(gamevotecounts,key=lambda x: x[1],reverse=True)

        for count in gamevotecounts:
            gamevotes.append((count[0],str(count[1])))


        randovotes.append(("Randomizer Name","Number of Votes"))
        randovotecounts = []
        for randovote in self.randovotes:
            found = False
            for count in randovotecounts:
                if count[0] == randovote[1]:
                    count[1]+=1
                    found = True
            if not found:
                randovotecounts.append([randovote[1],1])

        randovotecounts = sorted(randovotecounts,key=lambda x: x[1],reverse=True)

        for count in randovotecounts:
            randovotes.append((count[0],str(count[1])))
            
        tables.append(commands)
        tables.append(gamevotes)
        tables.append(randovotes)
        return tables

    def getParams(self):
        params=[]
        return params

    def setParam(self,param,val):
        pass

    def shouldRespond(self,msg,userLevel):
        if msg.messageType == 'PRIVMSG' and len(msg.msg)!=0:
            fullmsg = msg.msg.split()
            if fullmsg[0].lower()=="!gamevote" or fullmsg[0].lower()=="!randovote":
                return True

        if msg.messageType == 'PRIVMSG' and msg.sender in self.clearedgamevotes:
            return True

        if msg.messageType == 'PRIVMSG' and msg.sender in self.clearedrandovotes:
            return True
        
        return False

    def getCurGameVote(self,user):
        response = user+": You have not voted for any game"
        for voter in self.gamevotes:
            if voter[0].lower()==user.lower():
                response = user+": Your current vote is for '"+voter[1]+"'"
        return response

    def getCurRandoVote(self,user):
        response = user+": You have not voted for any randomizer"
        for voter in self.randovotes:
            if voter[0].lower()==user.lower():
                response = user+": Your current vote is for '"+voter[1]+"'"

        return response

    def getGameList(self):
        gamestatus=[]

        if self.credsAvailable:
            gamesResp = Session().get(self.gameUrl,headers={'Accept':'application/json'})
            gamesJson = json.loads(gamesResp.text)
            for game in gamesJson['values']:
                newGame = [game[0]]
                if len(game)==7:
                    newGame.append(game[6])
                else:
                    newGame.append("")
                gamestatus.append(newGame)
        return gamestatus

    def getRandoList(self):
        randostatus=[]

        if self.credsAvailable:
            randoResp = Session().get(self.randoUrl,headers={'Accept':'application/json'})
            randoJson = json.loads(randoResp.text)
            for game in randoJson['values']:
                newGame = [game[0]]
                if len(game)==6:
                    newGame.append(game[5])
                else:
                    newGame.append("")
                randostatus.append(newGame)
        return randostatus

    def loadVotes(self):
        voteFile = configDir+os.sep+self.bot.channel[1:]+os.sep+self.voteFile
        try:
            with open(voteFile,encoding='utf-8') as f:
                for line in f:
                    voteLine = line.strip().split()
                    if len(voteLine)>=3:
                        newVote = [voteLine[1]," ".join(voteLine[2:])]
                        if voteLine[0]=="game":
                            self.gamevotes.append(newVote)
                        elif voteLine[0]=="rando":
                            self.randovotes.append(newVote)
                    elif len(voteLine)>=2:
                        newVote = voteLine[1]
                        if voteLine[0]=="gameclear":
                            self.clearedgamevotes.append(newVote)
                        elif voteLine[0]=="randoclear":
                            self.clearedrandovotes.append(newVote)
                        
                            
        except FileNotFoundError:
            print(voteFile+" is not present, no votes loaded")

    def saveVotes(self):
        voteFile = configDir+os.sep+self.bot.channel[1:]+os.sep+self.voteFile
        with open(voteFile,mode='w',encoding='utf-8') as f:
            for vote in self.gamevotes:
                f.write("game "+vote[0]+" "+vote[1]+"\r\n")
            for vote in self.randovotes:
                f.write("rando "+vote[0]+" "+vote[1]+"\r\n")
            for vote in self.clearedgamevotes:
                f.write("gameclear "+vote+"\r\n")
            for vote in self.clearedrandovotes:
                f.write("randoclear "+vote+"\r\n")
        

    def tryGameVote(self,user,vote):
        response = user+": No game matching '"+vote+"' found"
        
        gameList = self.getGameList()

        for game in gameList:
            if vote.lower() in game[0].lower():
                if (game[1]==""):
                    response = user+": Your vote has been registered for '"+game[0]+"'"
                    found = False
                    for voter in self.gamevotes:
                        if voter[0].lower()==user.lower():
                            found = True
                    if found:
                        for voter in self.gamevotes:
                            if voter[0].lower()==user.lower():
                                voter[1] = game[0]
                    else:
                        newvote = [user.lower(),game[0]]
                        self.gamevotes.append(newvote)

                    self.saveVotes()
                else:
                    response = user+": '"+game[0]+"' has already been started and therefore cannot be voted for"
        return response

    def tryRandoVote(self,user,vote):
        response = user+": No game matching '"+vote+"' found"
        
        gameList = self.getRandoList()

        for game in gameList:
            if vote.lower() in game[0].lower():
                if (game[1]==""):
                    response = user+": Your vote has been registered for '"+game[0]+"'"
                    found = False
                    for voter in self.randovotes:
                        if voter[0].lower()==user.lower():
                            found = True
                    if found:
                        for voter in self.randovotes:
                            if voter[0].lower()==user.lower():
                                voter[1] = game[0]
                    else:
                        newvote = [user.lower(),game[0]]
                        self.randovotes.append(newvote)

                    self.saveVotes()
                else:
                    response = user+": '"+game[0]+"' has already been started and therefore cannot be voted for"
        return response


    def respond(self,msg,sock):
        response = ""
        fullmsg = msg.msg.split()

        gamevote = True

        if fullmsg[0].lower()=="!gamevote" or fullmsg[0].lower()=="!randovote":
            if (fullmsg[0].lower()=="!randovote"):
                gamevote = False

            if len(fullmsg)==1:
                if gamevote:
                    response = self.getCurGameVote(msg.sender)
                else:
                    response = self.getCurRandoVote(msg.sender)
            else:
                vote = " ".join(fullmsg[1:])
                if gamevote:
                    response = self.tryGameVote(msg.sender,vote)
                else:
                    response = self.tryRandoVote(msg.sender,vote)
        else:
            #Remind user that vote has been cleared
            clearedRando = False
            clearedGame = False

            if msg.sender.lower() in self.clearedrandovotes:
                clearedRando = True
                self.clearedrandovotes.remove(msg.sender)

            if msg.sender.lower() in self.clearedgamevotes:
                clearedGame = True
                self.clearedgamevotes.remove(msg.sender)

            if clearedRando and clearedGame:
                response = msg.sender+": Your votes have been cleared for both regular games and randomizers.  Please place new votes with !gamevote and !randovote"
            elif clearedRando:
                response = msg.sender+": Your randomizer vote has been cleared.  Please place a new vote with !randovote"
            elif clearedGame:
                response = msg.sender+": Your game vote has been cleared.  Please place a new vote with !gamevote"

            self.saveVotes()
            
        ircResponse = "PRIVMSG "+self.bot.channel+" : "+response+"\n"
        sock.sendall(ircResponse.encode('utf-8'))

        return response
