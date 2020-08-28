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
            votesUpdated = False

            for table in self.gameVoteCmd.voteTables:
                if not self.gameVoteCmd.voteTables[table].gameList:
                    #List must be populated before we should bother here
                    return

                votesToRemove = []
                for vote in self.gameVoteCmd.voteTables[table].votes:
                    found = False
                    gamelist = self.gameVoteCmd.voteTables[table].gameList
                    for game in gamelist:
                        if vote[1].lower() == game[0].lower():
                            if game[1]=="":
                                found = True
                    if not found:
                        votesToRemove.append(vote)
                        votesUpdated = True

                for vote in votesToRemove:
                    self.gameVoteCmd.voteTables.votes.remove(vote)
                    self.gameVoteCmd.voteTables.clearedVotes.append(vote[0])


            if votesUpdated:
                self.gameVoteCmd.saveVotes()
