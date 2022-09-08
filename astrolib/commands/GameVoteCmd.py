from astrolib.command import Command
from requests import Session
import json
import os
from time import sleep
import threading
from astrolib import BROADCASTER,NOTIF_CHANNELPOINTS

configDir="config"
gamevoteCredFile = "gamevotecreds.txt"

class GameVoteTable():
    def __init__(self,voteInfo,keyword,sheetName,gameCol,statusCol,firstRow):
        self.keyword = keyword
        self.voteInfo = voteInfo

        self.gameUrl = ""


        self.sheetName = sheetName
        self.gameColumn = gameCol
        self.statusColumn = statusCol
        self.firstRow = firstRow
        
        if self.voteInfo.credsAvailable:
            self.fullGameRange = self.sheetName+"!"+self.gameColumn+str(self.firstRow)+":"+self.statusColumn+"1000"
            self.gameUrl = "https://sheets.googleapis.com/v4/spreadsheets/"+self.voteInfo.sheetId+"/values/"+self.fullGameRange+"?key="+self.voteInfo.apiKey

        self.votes=[]
        self.bonusvotes=[]
        self.clearedVotes = []

        self.gameList = None
        self.updateGameList()

    def updateGameList(self):
        gamestatus=[]
        gamesJson = {}

        if self.voteInfo.credsAvailable:
            columnOffset = ord(self.statusColumn) - ord(self.gameColumn)

            try:
                gamesResp = Session().get(self.gameUrl,headers={'Accept':'application/json'})
                gamesJson = json.loads(gamesResp.text)
            except:
                return None
            
            if 'values' in gamesJson:
                for game in gamesJson['values']:

                    if len(game)==0:
                        return
                    
                    newGame = [game[0]]
                    if len(game)==columnOffset+1:
                        newGame.append(game[columnOffset])
                    else:
                        newGame.append("")
                    gamestatus.append(newGame)

                self.gameList = gamestatus

        return gamestatus
    
    def getCurVote(self,user):
        response = user+": You have not voted"
        for voter in self.votes:
            if voter[0].lower()==user.lower():
                response = user+": Your current vote is for '"+voter[1]+"'"

        return response
    
    def tryVote(self,user,vote,bonus=False):
        response = user+": No game matching '"+vote+"' found"
        found = False
        
        gameList = self.gameList

        if not gameList:
            response = "Please try again.  Game list has not been loaded yet"
            return (False,response)

        for game in gameList:
            if vote.lower() in game[0].lower():
                if (game[1]==""):
                    if not bonus:
                        response = user+": Your vote has been registered for '"+game[0]+"'"
                    else:
                        response = user+": Your bonus vote has been registered for '"+game[0]+"'"
                        
                    found = False
                    for voter in self.votes:
                        if voter[0].lower()==user.lower():
                            found = True
                    if found:
                        for voter in self.votes:
                            if voter[0].lower()==user.lower():
                                voter[1] = game[0]
                    else:
                        newvote = [user.lower(),game[0]]
                        if not bonus:
                            self.votes.append(newvote)
                        else:
                            self.bonusvotes.append(newvote)

                    self.voteInfo.saveVotes()
                else:
                    response = user+": '"+game[0]+"' has already been started and therefore cannot be voted for"

                break
            
        return (found,response)


class GameVoteCmd(Command):

    def gameListTask(self):
        while(True):
            for table in self.voteTables:
                #print("Updating "+table+" game list")
                self.voteTables[table].updateGameList()
                
            sleep(300)

    def __init__(self,bot,name):
        super(GameVoteCmd,self).__init__(bot,name)

        self.credsAvailable = False
        
        self.apiKey = self.bot.config["GameVote"]["googledocapikey"]
        self.sheetId = self.bot.config["GameVote"]["googlesheetid"]

        if self.apiKey != "":
            self.credsAvailable = True
            
        self.bot.subToNotification(NOTIF_CHANNELPOINTS,self.channelPointHandler)
            
        self.voteTables = dict()
            
        for configSection in self.bot.config:
            if "GameVoteTable" in configSection:
                keyword = configSection.replace("GameVoteTable","").lower()

                newTable = GameVoteTable(self,
                                         keyword,
                                         self.bot.config[configSection]["sheetname"],
                                         self.bot.config[configSection]["gamenamecolumn"],
                                         self.bot.config[configSection]["gamestatuscolumn"],
                                         self.bot.config[configSection]["firstgamerow"])

                self.voteTables[keyword] = newTable
                self.createBonusVoteReward(keyword)
        
        self.voteFile = "votes.txt"
        
        self.gameListThread = threading.Thread(target=self.gameListTask)
        self.gameListThread.start()

        self.loadVotes()

        #Register commands for all configured tables
        for table in self.voteTables:
            command = "!"+table+"vote"
            
            if not self.bot.isCmdRegistered(command):
                self.bot.regCmd(command,self)
            else:
                print(command+" is already registered to ",self.bot.getCmdOwner("command"))
            
    def createBonusVoteReward(self,keyword):
        title = "Bonus "+keyword+" vote"
        promptText = "Grants you a bonus "+keyword+" vote.  Specify the game name as you would with the normal vote commands"
        cost = 10000
        requireText = True

        rewards = self.bot.api.getCustomRewardList(self.bot.channelId)

        if title not in rewards.keys():
            if not self.bot.api.createCustomReward(self.bot.channelId,title,promptText,cost, requireText):
                print("Couldn't create 'Bonus "+keyword+" vote' reward - does it already exist?")
        else:
            if not self.bot.api.isCustomRewardModifiable(self.bot.channelId,title):
                print("ERROR: Custom Reward 'Bonus "+keyword+" vote' already exists, but isn't owned by Astronomibot - Please delete it")
                
    def channelPointHandler(self,data,sock):
        #print("Got: "+str(data))
        if data["reward"].startswith('Bonus ') and data["reward"].endswith(' vote'):
            votetablename = data["reward"].split("Bonus ")[1].split(" vote")[0]
            gamename = data["message"]
            print("It's a bonus vote on the "+votetablename+" table for "+gamename)

            result = self.voteTables[votetablename].tryVote(data["username"].lower(),gamename,True)
            baseResponse = result[1]
            success = result[0]

            if success:
                self.bot.api.fulfillChannelPointRedemption(data["redemptionid"],data["rewardid"],data["channelid"])
            else:
                self.bot.api.cancelChannelPointRedemption(data["redemptionid"],data["rewardid"],data["channelid"])

            response = "PRIVMSG "+self.bot.channel+" :"+baseResponse+"\n"
            sock.sendall(response.encode('utf-8'))
            return baseResponse
        
        

    def getDescription(self,full=False):
        listurl = 'https://docs.google.com/spreadsheets/d/'+self.sheetId
        if full and self.credsAvailable:
            return 'Let viewers vote for games and randomizers.  The list of games can be found here: <a href="'+listurl+'">Game List</a>'
        else:
            return 'Let viewers vote for games.  <a href="'+listurl+'">Game List</a>'
        
    def htmlInDesc(self):
        return True

    def getState(self):
        tables = []
        commands = []
        gamevotes = []
        randovotes = []

        commands.append(("Command Name","Description"))
        for table in self.voteTables:
            commands.append(("!"+table+"vote","Show your current vote"))
            commands.append(("!"+table+"vote [game]","Vote for the first game in the "+table+" spreadsheet that matches [game]"))
        tables.append(commands)

        for table in self.voteTables:
            gamevotes = []
            gamevotes.append((table.capitalize()+" Name","Number of Votes"))
            gamevotecounts = []
            for gamevote in self.voteTables[table].votes:
                found = False
                for count in gamevotecounts:
                    if count[0] == gamevote[1]:
                        count[1] = count[1]+1
                        found = True
                if not found:
                    gamevotecounts.append([gamevote[1],1])
                    
            for gamevote in self.voteTables[table].bonusvotes:
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

            tables.append(gamevotes)

        return tables

    def getParams(self):
        params=[]
        return params

    def setParam(self,param,val):
        pass

    def hasClearedVote(self,user):
        for table in self.voteTables:
            if user in self.voteTables[table].clearedVotes:
                return True
        return False

    def shouldRespond(self,msg,userLevel):
        if msg.messageType == 'PRIVMSG' and len(msg.msg)!=0:
            fullmsg = msg.msg.split()
            command = fullmsg[0].lower()
            if command.startswith("!") and command.endswith("vote"):
                keyword = command.replace("!","").replace("vote","")
                if keyword in self.voteTables:
                    return True

        if msg.messageType == 'PRIVMSG' and self.hasClearedVote(msg.sender):
            return True
        
        #if msg.messageType == 'PRIVMSG' and msg.sender in self.clearedgamevotes:
        #    return True

        #if msg.messageType == 'PRIVMSG' and msg.sender in self.clearedrandovotes:
        #    return True
        
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
        gamesJson = {}

        if self.credsAvailable:
            columnOffset = ord(self.statusColumn) - ord(self.gameColumn)

            try:
                gamesResp = Session().get(self.gameUrl,headers={'Accept':'application/json'})
                gamesJson = json.loads(gamesResp.text)
            except:
                return None
            
            if 'values' in gamesJson:
                for game in gamesJson['values']:
                    newGame = [game[0]]
                    if len(game)==columnOffset+1:
                        newGame.append(game[columnOffset])
                    else:
                        newGame.append("")
                    gamestatus.append(newGame)
        return gamestatus

    def getRandoList(self):
        randostatus=[]
        randoJson = {}

        if self.credsAvailable:
            columnOffset = ord(self.randoStatusColumn) - ord(self.randoGameColumn)
            try:
                randoResp = Session().get(self.randoUrl,headers={'Accept':'application/json'})
                randoJson = json.loads(randoResp.text)
            except:
                return None
            
            if 'values' in randoJson:
                for game in randoJson['values']:
                    newGame = [game[0]]
                    if len(game)==columnOffset+1:
                        newGame.append(game[columnOffset])
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

                        bonus=False
                        tablename = voteLine[0]
                        if tablename.startswith("bonus"):
                            bonus=True
                            tablename = tablename.lstrip("bonus")
                        
                        if tablename in self.voteTables:
                            if not bonus:
                                self.voteTables[tablename].votes.append(newVote)
                            else:
                                self.voteTables[tablename].bonusvotes.append(newVote)

                        else:
                            print("Unknown vote keyword: "+tablename)
                                
                    elif len(voteLine)>=2:
                        newVote = voteLine[1]
                        
                        keyword = voteLine[0].replace("clear","")
                        if keyword in self.voteTables:
                            self.voteTables[keyword].clearedVotes.append(newVote)
                        else:
                            print("Unknown vote clear keyword: "+keyword)

                        
                            
        except FileNotFoundError:
            print(voteFile+" is not present, no votes loaded")

    def saveVotes(self):
        voteFile = configDir+os.sep+self.bot.channel[1:]+os.sep+self.voteFile
        with open(voteFile,mode='w',encoding='utf-8') as f:
            for table in self.voteTables:
                for vote in self.voteTables[table].votes:
                    f.write(self.voteTables[table].keyword+" "+vote[0]+" "+vote[1]+"\r\n")
                for vote in self.voteTables[table].bonusvotes:
                    f.write("bonus"+self.voteTables[table].keyword+" "+vote[0]+" "+vote[1]+"\r\n")                
                for vote in self.voteTables[table].clearedVotes:
                    f.write(self.voteTables[table].keyword+"clear "+vote+"\r\n")

        

    def tryGameVote(self,user,vote):
        response = user+": No game matching '"+vote+"' found"
        
        gameList = self.gameList

        if not gameList:
            response = "Please try again.  Game list has not been loaded yet"
            return response

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

                break
            
        return response

    def tryRandoVote(self,user,vote):
        response = user+": No game matching '"+vote+"' found"
        
        gameList = self.randoList

        if not gameList:
            response = "Please try again.  Rando list has not been loaded yet"
            return response


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

                break
            
        return response


    def respond(self,msg,sock):
        response = ""
        fullmsg = msg.msg.split()
        
        command = fullmsg[0].lower()
        isCommand = command.startswith("!") and command.endswith("vote")
        keyword = command.replace("!","").replace("vote","")
        validCommand = keyword in self.voteTables

        if validCommand:

            if len(fullmsg)==1:
                response = self.voteTables[keyword].getCurVote(msg.sender)
            else:
                vote = " ".join(fullmsg[1:])
                result = self.voteTables[keyword].tryVote(msg.sender,vote)
                response = result[1]
        else:
            #Remind user that vote has been cleared
            clearedRando = False
            clearedGame = False

            clearedVoteCommands = []
            for table in self.voteTables:
                if msg.sender.lower() in self.voteTables[table].clearedVotes:
                    self.voteTables[table].clearedVotes.remove(msg.sender)
                    clearedVoteCommands.append("!"+table+"vote")
                    
            response = msg.sender+": Your votes have been cleared for the following commands: "+(", ".join(clearedVoteCommands))

            self.saveVotes()
            
        ircResponse = "PRIVMSG "+self.bot.channel+" : "+response+"\n"
        sock.sendall(ircResponse.encode('utf-8'))

        return response
