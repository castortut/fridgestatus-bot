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

{"updated": 1570918054.478339, "products": {'jäätelö': True, 'tölkki 2€': False}
"""



def getSwitchData():
    req = requests.get(CASTOR_API_URL)
    jsonreply = json.loads( req.content.decode("utf-8") )
    
    return jsonreply["updated"], jsonreply["products"]



def getUpdates(token, offset=0):
    url = BOT_BASE_URL + token + "/getUpdates" #+ "/getUpdates?timeout=100"
    params = {'offset':offset}
    req = requests.get(url, data=params)
    
    return json.loads( req.content.decode("utf-8") )



def sendMessage(token, chatID, msg):
    url = BOT_BASE_URL + token + "/sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(msg, chatID)
    
    if msg is not None:
        requests.get(url)

   
    
def formatStates(states):
    statedict = {}

    for key in states:
        if states[key] == True:
            statedict[key] = "jäljellä"
        else:
            statedict[key] = "loppu"
            
    return statedict



def cmdFridge(token, chatID):
    lastUpdated, states = getSwitchData()
    #lastUpdated = 7651687654.1
    #states = json.loads( '{"tuote1":false, "tuoteeeee2":true}' )

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



def writeLog(msg, addEndline=True):

    with open(LOG_FILE, "a") as f:
        f.write("\n")
        f.write(msg)
        
        if addEndline == True:
            f.write("\n---------------------------------------------\n")
        


def main():
    
    with open("./.token", "r") as f:
        token = f.read().rstrip(" \n")
        
        
    updateID = 0

    while True: 
        result = getUpdates(token, updateID)
        
        if result["ok"] == False:
            errCode = result["error_code"]
            errDesc = result["description"]
            
            writeLog( "{} Error {}: {}\n".format(datetime.now(), 
                                                 errCode, 
                                                 errDesc) )
            #print("no reply")             
            
            continue

        data = result["result"]
        
        if len(data) == 0:
            continue

        updateID = data[ len(data)-1 ]["update_id"] + 1
        
        
        command = ""
        chatID = ""
        
        try:
            command = data[len(data)-1]["message"]["text"]
            pass

        # action message was send (bot/person was removed/added etc)
        except KeyError:
            writeLog("json reply parse error, reply: ", False)
            writeLog( json.dumps(data[len(data)-1], indent=4, sort_keys=True) )
                
                
        chatID = data[len(data)-1]["message"]["chat"]["id"]
        command = command.lstrip("/").replace("@CastorFridgeBot", " ").rstrip(" ").lower()
        
        
        if command == "fridge":
            cmdFridge(token, chatID)



    
if __name__ == "__main__":
    main()

