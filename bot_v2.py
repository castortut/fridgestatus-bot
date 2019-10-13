import sys
import os
import json
import requests
from datetime import datetime

BOT_BASE_URL = "https://api.telegram.org/bot"
CASTOR_API_URL = "https://fridge0.api.avaruuskerho.fi/"
LOG_FILE = "log.txt"

"""
Example reply from api:

{"updated": 1570918054.478339, "switches": [tuote1:false, tuote2:true]}
"""

# TODO: error loggin in exception
# TODO: replace dummy json with data from getSwitchData()


def getSwitchData():
    req = requests.get(CASTOR_API_URL)
    jsonreply = json.loads( req.content.decode("utf-8") )
    
    return jsonreply["updated"], jsonreply["switches"]



def getUpdates(token, offset=None):
    url = BOT_BASE_URL + token + "/getupdates" #+ "/getUpdates?timeout=100"
    
    if offset:
        url += "&offset={}".format(offset + 1)
        
    req = requests.get(url)
    
    return json.loads( req.content.decode("utf-8") )



def sendMessage(token, chatID, msg):
    url = BOT_BASE_URL + token + "/sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(msg, chatID)
    
    if msg is not None:
        requests.get(url)

   
    
def formatStates(states):
    statedict = {}

    for key in states:

        if key == True:
            statedict[key] = "jäljellä"
        else:
            statedict[key] = "loppu"
            
    return statedict



def cmdFridge(token, chatID):
    #lastUpdated, states = getSwitchData()
    lastUpdated = 7651687654.1
    states = json.loads( '{"tuote1":false, "tuoteeeee2":true}' )

    lastUpdated = datetime.utcfromtimestamp(lastUpdated).strftime("%d.%m.%Y %H:%M:%S")
    states = formatStates(states)

    maxlength = 0
    for item in states:
        
        if len(item) > maxlength:
            maxlength = len(item)


    message = ""
    for item in sorted(states.keys()):
        space = " " * ( maxlength - len(item) )
        message += "{}: {}{}\n".format(item, space, states[item])

    message += "\nPäivitetty " + lastUpdated + "\n"

    # add monospace
    message = "```\n" + message + "\n```"

    sendMessage(token, chatID, message)



def main():
    
    with open("./.token", "r") as tokenFile:
        token = tokenFile.read().rstrip("\n")
        
    handled = []    

    while True: 
        result = getUpdates(token)
        
        if result["ok"] == False:
            errCode = result["error_code"]
            errDesc = result["description"]
            
            print("Error {}: {}".format(errCode, errDesc) )
            break

        
        data = result["result"]
        msgID = data[len(data)-1]["message"]["message_id"]
        
        if msgID in handled:
            continue
            
        if len(handled) > 1000:
            handled.clear()
            
        command = ""
        chatID = ""
        
        try:
            command = data[len(data)-1]["message"]["text"]
        
        # action message was send (bot/person was removed/added etc)
        except KeyError:
            
            with open(LOG_FILE) as f:
                msg = data[len(data)-1]
                
                f.write("--------------------------------------------------")
                f.write(msg)
                f.write("json reply parse error\n")
                f.write( json.dumps(msg, indent=4, sort_keys=True) )
                f.write("--------------------------------------------------")
            
        
        chatID = data[len(data)-1]["message"]["chat"]["id"]
        command = command.lstrip("/").replace("@CastorFridgeBot", " ").rstrip(" ").lower()

        if command == "fridge":
            cmdFridge(token, chatID)


        handled.append(msgID)
                
    
if __name__ == "__main__":
    main()

