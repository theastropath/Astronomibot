EVERYONE = 1
REGULAR = 2
MOD = 3
BROADCASTER = 4

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
