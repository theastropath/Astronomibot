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
        except:
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

    def setGame(self, channelId, game):
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
        if channelId is None:
            return ""
        try:
            result = self._authRequest("https://api.twitch.tv/kraken/channels/%s" % channelId)
            return result["status"] if result else ""

        except HTTPError as e:
            print("getTitle: "+str(e))
        return ""

    def getChannelUrl(self,channelId):
        if channelId is None:
            return ""
        try:
            result = self._authRequest("https://api.twitch.tv/kraken/channels/%s" % channelId)
            return result["url"] if result else ""

        except HTTPError as e:
            print("getChannelUrl: "+str(e))
        return ""



    def getTwitchEmotes(self):
        return self._pubRequest('https://api.twitch.tv/kraken/chat/emoticons')['emoticons']

    def isStreamOnline(self, channelId):
        if channelId == None:
            return False
        try:
            streamState = self._idedRequest("https://api.twitch.tv/kraken/streams/"+channelId)
            if 'stream' in streamState:
                return streamState['stream'] is not None

        except HTTPError as e:
            print("isStreamOnline "+str(e))

        except ConnectionError as e:
            print("isStreamOnline "+str(e))

        return False

    def getStreamLiveTime(self, channelId):
        try:
            streamState = self._idedRequest("https://api.twitch.tv/kraken/streams/"+channelId)
            if 'stream' in streamState:
                if streamState['stream'] is not None:
                    liveTime = streamState['stream']['created_at']
                    return time.strptime(liveTime, '%Y-%m-%dT%H:%M:%SZ')

        except HTTPError as e:
            print("getStreamLiveTime: "+str(e))

        return None

    def getChannelId(self):
        try:
            channels = self._authRequest("https://api.twitch.tv/kraken/channel")
            chanId = channels['_id']
            return chanId

        except HTTPError as e:
            print("getChannelId: "+str(e))

        return None

    def getChannelIdFromName(self,username):
        try:
            users = self._idedRequest("https://api.twitch.tv/kraken/users?login="+username+"&api_version=5")
            if 'users' in users:
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
