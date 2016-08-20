#!/usr/bin/python

import xml.etree.ElementTree as ET
import cgi, sys, json
import clueengine

def error(s):
    print "Content-type: application/json\n\n"
    print '{"errorStatus": 1, "errorText": "%s"}' % s
    sys.exit(0)

def success(s):
    print "Content-type: application/json\n\n"
    print '{"errorStatus": 0, %s}' % s
    sys.exit(0)

def getClauseInfo(engine):
    info = {}
    for i in range(engine.numPlayers):
        curInfo = []
        for clause in engine.players[i].possibleCards:
            curInfo.append(list(clause))
        if len(curInfo) > 0:
            info[repr(i)] = curInfo
    return info

def getInfoFromChangedCards(engine, changedCards):
    info = []
    for card in changedCards:
        possibleOwners = list(engine.whoHasCard(card))
        if len(possibleOwners) == 1:
            owner = possibleOwners[0]
            if (owner == engine.numPlayers):
                status = 2
            else:
                status = 1
            info.append({"card": card, "status": status, "owner":possibleOwners})
        else:
            if engine.numPlayers in possibleOwners:
                status = 0
            else:
                status = 1
            info.append({"card": card, "status": status, "owner":possibleOwners}) 
    return info
form = cgi.FieldStorage()
action = None
if (form.has_key('action')):
    action = form.getfirst('action')
else:
    error("Internal error - No action specified!")
# Valid actions are 'new', 'whoOwns', 'suggestion', 'fullInfo', 'simulate' ('accusation' in the future?)
if (action != 'new' and action != 'whoOwns' and action != 'suggestion' and action != 'fullInfo' and action != 'simulate'):
    error("Internal error - invalid action '%s'!" % action)
if (action != 'new' and (not form.has_key('sess'))):
    error("Internal error - missing sess!")
if (action != 'new'):
    (engine, s) = clueengine.ClueEngine.loadFromString(form.getfirst('sess'))
    if (s != ''):
        error("Internal error - invalid session string '%s'!" % form.getfirst('sess'))
else:
    if (not form.has_key('players')):
        error("Internal error - action new without players!")
    numPlayers = int(form.getfirst('players'))
    engine = clueengine.ClueEngine(numPlayers)
    for i in range(numPlayers):
        if (not form.has_key('numCards%d' % i)):
            error("Internal error - action new missing key numCards%d!" % i)
        numP = int(form.getfirst('numCards%d' % i))
        engine.players[i].numCards = numP
if (action == 'new'):
    # This is all we have to do.
    success('"session": "%s"' % engine.writeToString())
if (action == 'whoOwns'):
    # See who owns what.
    if (not form.has_key('owner') or not form.has_key('card')):
        error("Internal error: action=whoOwns, missing owner or card!")
    owner = int(form.getfirst('owner'))
    card = form.getfirst('card')
    changedCards = engine.infoOnCard(owner, card, True)
    success('"newInfo": %s, "clauseInfo": %s, "session": "%s", "isConsistent": %s' % (json.write(getInfoFromChangedCards(engine, changedCards)), json.write(getClauseInfo(engine)), engine.writeToString(), json.write(engine.isConsistent())))
if (action == 'suggestion'):
    # See what the suggestion is
    if (not form.has_key('suggestingPlayer') or not form.has_key('card1') or not form.has_key('card2') or not form.has_key('card3') or not form.has_key('refutingPlayer') or not form.has_key('refutingCard')):
        error("Internal error: action=whoOwns, missing suggestingPlayer, card1, card2, card3, refutingPlayer, or refutingCard!")
    suggestingPlayer = int(form.getfirst('suggestingPlayer'))
    card1 = form.getfirst('card1')
    card2 = form.getfirst('card2')
    card3 = form.getfirst('card3')
    refutingPlayer = int(form.getfirst('refutingPlayer'))
    refutingCard = form.getfirst('refutingCard')
    if (refutingPlayer == -1):
        refutingPlayer = None
    if (refutingCard == "None"):
        refutingCard = None
    changedCards = engine.suggest(suggestingPlayer, card1, card2, card3, refutingPlayer, refutingCard)
    success('"newInfo": %s, "clauseInfo": %s, "session": "%s", "isConsistent": %s' % (json.write(getInfoFromChangedCards(engine, changedCards)), json.write(getClauseInfo(engine)), engine.writeToString(), json.write(engine.isConsistent())))
if (action == 'fullInfo'):
    success('"newInfo": %s, "clauseInfo": %s, "session": "%s", "numPlayers": %d, "numCards": %s, "isConsistent": %s' % (json.write(getInfoFromChangedCards(engine, reduce(lambda x, y: x+y, [engine.cards[x] for x in engine.cards]))), json.write(getClauseInfo(engine)), engine.writeToString(), engine.numPlayers, json.write([x.numCards for x in engine.players[:-1]]), json.write(engine.isConsistent())))
if (action == 'simulate'):
    success('"simData": %s' % json.write(engine.getSimulationData()))
