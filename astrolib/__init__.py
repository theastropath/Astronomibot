EVERYONE = 1
REGULAR = 2
MOD = 3
BROADCASTER = 4

NOTIF_CHANNELPOINTS = "channel-points"
NOTIF_BITSEVENT = "bits"
NOTIF_SUBSCRIPTION = "subscription"
NOTIF_TYPES = [NOTIF_CHANNELPOINTS,NOTIF_BITSEVENT,NOTIF_SUBSCRIPTION]

replaceTerm="$REPLACE"
countTerm="$COUNT"
referenceCountTerm="$REF"

def userLevelToStr(userLevel):
    if userLevel == EVERYONE:
        return "Everyone"
    elif userLevel == REGULAR:
        return "Regular Viewer"
    elif userLevel == MOD:
        return "Moderator"
    elif userLevel == BROADCASTER:
        return "Broadcaster"
    else:
        return "???"
