import time
import json
from urllib.parse import urlencode
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError, InvalidURL, ConnectionError

class TwitchApi:
    def __init__(self, clientId, accessToken, clientSecret):
        self.clientId = clientId
        self.accessToken = accessToken
        self.clientSecret = clientSecret
        self.session = Session()

        #Allow 2 retries on all API requests
        retryAdapter = HTTPAdapter(max_retries=2)
        self.session.mount('https://',retryAdapter)
        self.session.mount('http://',retryAdapter)


    def _pubRequest(self, url):
        response = self.session.get(url,headers={
        'Accept': 'application/vnd.twitchtv.v5+json',
        })
        try:
            return json.loads(response.text)
        except:
            return None

    def _idedRequest(self, url):
        response = self.session.get(url, headers={
        'Client-ID': self.clientId,
        'Accept': 'application/vnd.twitchtv.v5+json',
        })
        try:
            result = json.loads(response.text)
        except Exception as e:
            result = None

        return result

    def _authRequest(self, url, data=None, method='GET'):
        if data is not None:
            data = json.dumps(data).encode('utf-8')

        response = self.session.request(method, url, data=data, headers={
            'Client-ID': self.clientId,
            'Accept': 'application/vnd.twitchtv.v5+json',
            'Authorization': 'OAuth '+self.accessToken,
            'Content-Type': 'application/json'
        })
        try:
            return json.loads(response.text)
        except:
            return None
        
    def _helixRequest(self, url, data=None, method='GET',timeout=5):
        if data is not None:
            data = json.dumps(data).encode('utf-8')

        response = self.session.request(method, url, data=data, timeout=timeout, headers={
            'Client-ID': self.clientId,
            'Authorization': 'Bearer '+self.accessToken,
            'Content-Type': 'application/json'
        })
        try:
            result = json.loads(response.text)
            return result
        except:
            return None
        
    def setGame(self, channelId, game):
        print("setGame DEPRECATED")
        if channelId is None:
            return False

        data = {"channel": {"game": game}}
        try:
            result = self._authRequest("https://api.twitch.tv/kraken/channels/%s" % channelId, data, 'PUT')
            return True

        except HTTPError as e:
            print("setGame: "+str(e))

        return False

    def setTitle(self, channelId, title):
        print("setTitle DEPRECATED")
        if channelId is None:
            return False

        data = {"channel": {"status": title}}
        try:
            result = self._authRequest("https://api.twitch.tv/kraken/channels/%s" % channelId, data, 'PUT')
            return True

        except HTTPError as e:
            print("setTitle: "+str(e))

        return False

    def getTitle(self,channelId):
        print("getTitle DEPRECATED")
        
        if channelId is None:
            return ""
        try:
            result = self._authRequest("https://api.twitch.tv/kraken/channels/%s" % channelId)
            return result["status"] if result else ""

        except HTTPError as e:
            print("getTitle: "+str(e))
        return ""

    def getChannelUrl(self,channelId):
        print("getChannelUrl DEPRECATED")
        if channelId is None:
            return ""
        try:
            result = self._authRequest("https://api.twitch.tv/kraken/channels/%s" % channelId)
            return result["url"] if result else ""

        except HTTPError as e:
            print("getChannelUrl: "+str(e))
        return ""



    def getTwitchEmotes(self):
        print("getTwitchEmotes DEPRECATED")
        emotes = self._idedRequest('https://api.twitch.tv/kraken/chat/emoticons')
        if emotes is not None and "emoticons" in emotes.keys():
            return emotes['emoticons']
        else:
            print("Couldn't fetch emotes")
            return None
        
    def getTwitchEmotes2(self):
        print("getTwitchEmotes2 DEPRECATED")
        emotes = self._idedRequest('https://api.twitch.tv/kraken/chat/emoticon_images')
        if emotes is not None and "emoticons" in emotes.keys():
            return emotes['emoticons']
        else:
            print("Couldn't fetch emotes")
            return None
        
    def isStreamOnline(self, channelId):
        print("isStreamOnline DEPRECATED")
        if channelId == None:
            return False
        try:
            streamState = self._idedRequest("https://api.twitch.tv/kraken/streams/"+channelId)
            if streamState and 'stream' in streamState:
                return streamState['stream'] is not None

        except HTTPError as e:
            print("isStreamOnline "+str(e))

        except ConnectionError as e:
            print("isStreamOnline "+str(e))

        return False

    def getStreamLiveTime(self, channelId):
        print("getStreamLiveTime DEPRECATED")

        try:
            streamState = self._idedRequest("https://api.twitch.tv/kraken/streams/"+channelId)
            if streamState and 'stream' in streamState:
                if streamState['stream'] is not None:
                    liveTime = streamState['stream']['created_at']
                    return time.strptime(liveTime, '%Y-%m-%dT%H:%M:%SZ')

        except HTTPError as e:
            print("getStreamLiveTime: "+str(e))

        return None

    def getChannelId(self):
        print("getChannelId DEPRECATED")
        try:
            channels = self._authRequest("https://api.twitch.tv/kraken/channel")
            chanId = channels['_id']
            return chanId

        except HTTPError as e:
            print("getChannelId: "+str(e))

        return None

    def getChannelIdFromName(self,username):
        print("getChannelIdFromName DEPRECATED")
        try:
            users = self._idedRequest("https://api.twitch.tv/kraken/users?login="+username+"&api_version=5")
            if users and 'users' in users:
                for user in users['users']:
                    if  user['name'] == username and '_id' in user:
                        chanId = user['_id']
                        return chanId

        except HTTPError as e:
            print("getChannelIdFromName: "+str(e))

        return None

    def isHosting(self, channelId):
        if channelId is None:
            return False

        try:
            hostsList = self._pubRequest("https://tmi.twitch.tv/hosts?"+urlencode({'include_logins': '1', 'host': channelId}))
            if hostsList and 'hosts' in hostsList:
                return 'target_login' in hostsList['hosts'][0]

        except HTTPError as e:
            print("isHosting: "+str(e))

        return False

    def getCurrentlyHostedChannel(self, channelId):
        if channelId is None:
            return None

        try:
            hostsList = self._pubRequest("https://tmi.twitch.tv/hosts?"+urlencode({'include_logins': '1', 'host': channelId}))
            host = hostsList['hosts'][0]
            return host.get('target_login', None)

        except HTTPError as e:
            print("getCurrentlyHostedChannel: "+str(e))

        return None

    def getChatters(self, channelName):
        try:
            chatlist = self._pubRequest('http://tmi.twitch.tv/group/user/%s/chatters' % channelName.lower())
            if chatlist and 'chatters' in chatlist:
                return chatlist['chatters']

        except HTTPError as e:
            #This API is particularly prone to responding with a 503,
            #so we don't want to constantly be printing the error out
            #print("getChatters: "+str(e))
            pass
            
        except InvalidURL as e:
            print("getChatters: "+str(e))

        return None

    def getAllChatters(self, channelName):
        allchatters = None
        chatterMap = self.getChatters(channelName)

        if chatterMap:
            allchatters = []
            for chatters in chatterMap.values():
                allchatters.extend(chatters)

        return allchatters

    def getModerators(self, channelName):
        chatterMap = self.getChatters(channelName)
        return chatterMap["moderators"] if chatterMap else []


    def getStreamFromNameHelix(self,username):
        try:
            stream = self._helixRequest("https://api.twitch.tv/helix/streams?user_login="+username)
            return stream
        except HTTPError as e:
            print("getStreamFromNameHelix: "+str(e))

        return None
    
    def getStreamFromNameListHelix(self,namelist):
        try:
            url = "https://api.twitch.tv/helix/streams?"
            for name in namelist:
                url=url+"user_login="+name+"&"
            stream = self._helixRequest(url)
            #print(str(stream))
            return stream
        except HTTPError as e:
            print("getStreamFromNameListHelix: "+str(e))

        return None

    def getChannelFromIdHelix(self,broadcaster_id):
        try:
            channel = self._helixRequest("https://api.twitch.tv/helix/channels?broadcaster_id="+broadcaster_id)
            #print(str(channel))
            return channel
        except HTTPError as e:
            print("getChannelFromIdHelix: "+str(e))

        return None
    
    def getUserIdFromNameHelix(self,name):
        try:
            user = self._helixRequest("https://api.twitch.tv/helix/users?login="+name)
            #print(str(user))
            if len(user["data"])!=0:
                info = user["data"][0]
                if "id" in info:
                    return info["id"]
        except HTTPError as e:
            print("getChannelFromIdHelix: "+str(e))

        return None
    
    def getChannelFromNameHelix(self,name):
        userid = self.getUserIdFromNameHelix(name)
        if userid:
            try:
                channel = self._helixRequest("https://api.twitch.tv/helix/channels?broadcaster_id="+userid)
                return channel
            except HTTPError as e:
                print("getChannelFromIdHelix: "+str(e))

        return None

    def isStreamOnlineHelix(self,username):
        stream = self.getStreamFromNameHelix(username)
        if stream:
            if "data" in stream:
                return len(stream["data"])!=0
        return False

    def areStreamsOnlineHelix(self,namelist):
        stream = self.getStreamFromNameListHelix(namelist)
        onlineList = []
        if stream:
            if "data" in stream:
                for stream in stream["data"]:
                    if "user_name" in stream:
                        onlineList.append(stream["user_name"].lower())
                        #print(stream["user_name"])
        return onlineList

    def getStreamLiveTimeHelix(self, username):
        stream = self.getStreamFromNameHelix(username)
        if stream:
            if "data" in stream:
                if len(stream["data"])!=0:
                    liveTime = stream["data"][0]['started_at']
                    return time.strptime(liveTime, '%Y-%m-%dT%H:%M:%SZ')
        return None

    def getChannelIdHelix(self):
        try:
            user = self._helixRequest("https://api.twitch.tv/helix/users")
            #print(str(user))
            if len(user["data"])!=0:
                info = user["data"][0]
                if "id" in info:
                    return info["id"]
        except HTTPError as e:
            print("getChannelFromIdHelix: "+str(e))

        return None

    def getChannelUrlFromIdHelix(self,userid):
        channel = self.getChannelFromIdHelix(userid)
        if channel and "data" in channel and len(channel["data"])!=0:
            channelname = channel["data"][0]["broadcaster_name"]
            return "https://Twitch.tv/"+channelname
        return None

    def getChannelUrlFromNameHelix(self,username):
        channel = self.getChannelFromNameHelix(username)
        if channel and "data" in channel and len(channel["data"])!=0:
            channelname = channel["data"][0]["broadcaster_name"]
            return "https://Twitch.tv/"+channelname
        return None
        
    def getTitleByNameHelix(self,username):
        channel = self.getChannelFromNameHelix(username)
        if channel and ("data" in channel) and len(channel["data"])!=0:
            return channel["data"][0]["title"]
        return ""

    def getGameByNameHelix(self,username):
        channel = self.getChannelFromNameHelix(username)
        if channel and ("data" in channel) and len(channel["data"])!=0:
            return channel["data"][0]["game_name"]
        return ""

    def getGameIdByNameHelix(self,gamename):
        try:
            game = self._helixRequest("https://api.twitch.tv/helix/games?name="+gamename)
            if game and ("data" in game) and len(game["data"])!=0:
                return game["data"][0]["id"]
            #print(str(game))
        except HTTPError as e:
            print("getGameIdByNameHelix: "+str(e))

        return None
        

    def setGameByIdHelix(self,channelId,game):
        gameId = self.getGameIdByNameHelix(game)
        if gameId == None:
            return False
        data = {"game_id": gameId}
        try:
            result = self._helixRequest("https://api.twitch.tv/helix/channels?broadcaster_id=%s" % channelId, data, 'PATCH')
            #print(str(result))
            return True

        except HTTPError as e:
            print("setGameByNameHelix: "+str(e))

        return False

    def setGameByNameHelix(self,username,game):
        channelId = self.getUserIdFromNameHelix(username)
        if channelId:
            return self.setGameByIdHelix(channelId,game)
        return False
    
    def setTitleByIdHelix(self,channelId,title):
        data = {"title": title}
        try:
            result = self._helixRequest("https://api.twitch.tv/helix/channels?broadcaster_id=%s" % channelId, data, 'PATCH')
            #print(str(result))
            return True

        except HTTPError as e:
            print("setTitleByNameHelix: "+str(e))

        return False

    def setTitleByNameHelix(self,username,title):
        channelId = self.getUserIdFromNameHelix(username)
        if channelId:
            return self.setTitleByIdHelix(channelId,title)
        return False

    #Redemption status can only be updated if the reward was created by your client ID, so make sure to check if you can modify it
    #before using this API (ie. check with isCustomRewardModifiable first)
    def updateChannelPointRedemptionStatus(self,redeemId,rewardId,channelId,status):
        data = {"status": status}
        try:
            result = self._helixRequest("https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions?broadcaster_id=%s&reward_id=%s&id=%s" % (channelId,rewardId,redeemId), data, 'PATCH')
            #print(str(result))
            return True

        except HTTPError as e:
            print("updateChannelPointRedemptionStatus: "+str(e))

        return False

    def fulfillChannelPointRedemption(self,redeemId,rewardId,channelId):
        return self.updateChannelPointRedemptionStatus(redeemId,rewardId,channelId,"FULFILLED")
    
    def cancelChannelPointRedemption(self,redeemId,rewardId,channelId):
        return self.updateChannelPointRedemptionStatus(redeemId,rewardId,channelId,"CANCELED")

    #You can't create duplicate rewards, so before creating one, you should check if it exists, and also that you can modify it
    #(If you want to be able to cancel and refund the rewards if things go wrong)
    def createCustomReward(self,channelId,title,prompt,cost, requireText):
        data = {"title": title,"prompt":prompt,"cost":cost,"is_user_input_required":str(requireText)}
        try:
            result = self._helixRequest("https://api.twitch.tv/helix/channel_points/custom_rewards?broadcaster_id=%s" % channelId, data, 'POST')
            #print(str(result))
            return True

        except HTTPError as e:
            print("createCustomReward: "+str(e))

        return False

    def getCustomRewardList(self,channelId):
        try:
            rewards = self._helixRequest("https://api.twitch.tv/helix/channel_points/custom_rewards?broadcaster_id=%s" % channelId)
            #print(str(rewards))
            if "data" in rewards:
                rewardDict = dict()
                for reward in rewards["data"]:
                    #print(reward["title"])
                    rewardDict[reward["title"]]=reward

                #print(str(rewardDict.keys()))
                return rewardDict

        except HTTPError as e:
            print("getCustomRewardList: "+str(e))

        return None

    #Twitch, in their infinite wisdom, made it such that you can only touch rewards that were created by your client ID (NOT just a matching user)
    #Of course, they also didn't provide a way to check if you are able to modify an existing reward, or check what client ID created it.
    #By "updating" the reward with an identical title, we are either allowed to do it, or get a "Forbidden" error if we aren't allowed.
    #Note that if we don't pass in any fields to modify, it responds successfully, as though we are allowed to modify the reward.
    def isCustomRewardModifiable(self,channelId,rewardName):
        data = {"title": rewardName}
        rewardId = ""

        rewards = self.getCustomRewardList(channelId);
        if rewardName in rewards:
            rewardId = rewards[rewardName]["id"]
        else:
            return False

        try:
            result = self._helixRequest("https://api.twitch.tv/helix/channel_points/custom_rewards?broadcaster_id=%s&id=%s" % (channelId,rewardId),data, 'PATCH')
            #print("Modifiable? "+str(result))
            if "data" in result and "error" not in result:
                return True

        except HTTPError as e:
            print("isCustomRewardModifiable: "+str(e))

        return False
    
