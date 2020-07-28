from astrolib.feature import Feature

class GameVoteFeature(Feature):
    def __init__(self,bot,name):
        super(GameVoteFeature,self).__init__(bot,name)
        self.gameVoteCmd = self.bot.commands["GameVoteCmd"]

        self.gameVoteFreq = 600
        self.gameVoteUpdate = 1


    def handleFeature(self,sock):
        self.gameVoteUpdate = self.gameVoteUpdate - 1
        if self.gameVoteUpdate == 0:
            self.gameVoteUpdate = self.gameVoteFreq
            #gamelist = self.gameVoteCmd.getGameList()
            #randolist = self.gameVoteCmd.getRandoList()
            gamelist = self.gameVoteCmd.gameList
            randolist = self.gameVoteCmd.randoList
            votesUpdated = False

            if not gamelist or not randolist:
                #Both lists must be populated before we should bother here
                return

            votesToRemove = []
            for vote in self.gameVoteCmd.gamevotes:
                found = False
                for game in gamelist:
                    if vote[1].lower() == game[0].lower():
                        if game[1]=="":
                            found = True
                if not found:
                    votesToRemove.append(vote)
                    votesUpdated = True

            for vote in votesToRemove:
                self.gameVoteCmd.gamevotes.remove(vote)
                self.gameVoteCmd.clearedgamevotes.append(vote[0])

            
            votesToRemove = []
            for vote in self.gameVoteCmd.randovotes:
                found = False
                for game in randolist:
                    if vote[1].lower() == game[0].lower():
                        if game[1]=="":
                            found = True
                if not found:
                    votesToRemove.append(vote)
                    votesUpdated = True

            for vote in votesToRemove:
                self.gameVoteCmd.randovotes.remove(vote)
                self.gameVoteCmd.clearedrandovotes.append(vote[0])

            if votesUpdated:
                self.gameVoteCmd.saveVotes()
