import time
import json
import urllib
from urllib.request import urlopen
from urllib.parse import urlencode

class TwitchApi:
    def __init__(self, clientId, accessToken, clientSecret):
        self.clientId = clientId
        self.accessToken = accessToken
        self.clientSecret = clientSecret

    def _pubRequest(self, url):
        response = urlopen(url)
        return json.loads(response.read().decode('utf-8'))

    def _idedRequest(self, url):
        req = urllib.request.Request(url)
        req.add_header('Client-ID', self.clientId)

        response = urllib.request.urlopen(req)
        stream = response.read().decode()
        result = json.loads(stream)
        return result

    def _authRequest(self, url, data=None, method='GET'):
        if data is not None:
            data = json.dumps(data).encode('utf-8')

        req = urllib.request.Request(url=url, data=data, method=method)
        req.add_header('Client-ID', self.clientId)
        req.add_header('Accept', "application/vnd.twitchtv.v5+json")
        req.add_header('Authorization', "OAuth "+self.accessToken)
        req.add_header('Content-Type', "application/json")

        response = urllib.request.urlopen(req)
        stream = response.read().decode('utf-8')
        return json.loads(stream)

    def setGame(self, channeId, game):
        if channeId is None:
            return False

        data = {"channel": {"game": game}}
        try:
            result = self._authRequest("https://api.twitch.tv/kraken/channels/%s" % channeId, data, 'PUT')
            return True

        except urllib.error.HTTPError as e:
            print(e)

        return False

    def setTitle(self, channeId, title):
        if channeId is None:
            return False

        data = {"channel": {"status": title}}
        try:
            result = self._authRequest("https://api.twitch.tv/kraken/channels/%s" % channeId, data, 'PUT')
            return True

        except urllib.error.HTTPError as e:
            print(e)

        return False

    def getTwitchEmotes(self):
        return self._pubRequest('https://api.twitch.tv/kraken/chat/emoticons')['emoticons']

    def isStreamOnline(self, channelName):
        try:
            streamState = self._idedRequest("https://api.twitch.tv/kraken/streams/"+channelName)
            return streamState['stream'] is not None

        except urllib.error.HTTPError as e:
            print(e)

        return False

    def getStreamLiveTime(self, channelName):
        try:
            streamState = self._idedRequest("https://api.twitch.tv/kraken/streams/"+channelName)
            if streamState['stream'] is not None:
                liveTime = streamState['stream']['created_at']
                return time.strptime(liveTime, '%Y-%m-%dT%H:%M:%SZ')

        except urllib.error.HTTPError as e:
            print(e)

        return None

    def getChannelId(self, channelName):
        try:
            channels = self._idedRequest("https://api.twitch.tv/kraken/channels/"+channelName)
            channelsVal = json.loads(channels)
            chanId = channelsVal['_id']
            return chanId

        except urllib.error.HTTPError as e:
            print(e)

        return None

    def isHosting(self, channeId):
        if channeId is None:
            return False

        try:
            hostsList = self._pubRequest("https://tmi.twitch.tv/hosts?"+urlencode({'include_logins': '1', 'host': channelId}))
            return 'target_login' in hostsList['hosts'][0]

        except urllib.error.HTTPError as e:
            print(e)

        return False

    def getCurrentlyHostedChannel(self, channelId):
        if channeId is None:
            return None

        try:
            hostsList = self._pubRequest("https://tmi.twitch.tv/hosts?"+urlencode({'include_logins': '1', 'host': channelId}))
            host = hostsList['hosts'][0]
            return host.get('target_login', None)

        except urllib.error.HTTPError as e:
            print(e)

        return None

    def getChatters(self, channelName):
        try:
            chatlist = self._pubRequest('http://tmi.twitch.tv/group/user/%s/chatters' % channelName.lower())

            return chatlist['chatters']

        except urllib.error.HTTPError as e:
            print(e)

        except urllib.error.URLError as e:
            print(e)

        return None

    def getAllChatters(self, channelName):
        allchatters = []
        chatterMap = self.getChatters(channelName)

        if chatterMap:
            for chatters in chatterMap.values():
                allchatters.extend(chatters)

        return allchatters

    def getModerators(self, channelName):
        chatterMap = self.getChatters(channelName)
        return chatterMap["moderators"] if chatterMap else []
