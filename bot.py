import sys
import os
import json
import requests
from datetime import datetime
import time

BOT_BASE_URL = "https://api.telegram.org/bot"
CASTOR_API_URL = "https://fridge0.api.avaruuskerho.fi/"
LOG_FILE = "log.txt"


def getSwitchData():
    """Query fridge switch data from castor fridgestatus api
    
    
    Example reply from api:

        {
            "updated": 1570918054.478339, 
            "products": 
                {
                    'jäätelö': True, 
                    'tölkki': False
                }
        }
    
    Returns:
        timeUpdated (float): unix time of last update of switches' states
        states (dict):       switch states as dict, e.g. {'jäätelö':False}
    
    """
    
    req = requests.get(CASTOR_API_URL)
    jsonreply = json.loads( req.content.decode("utf-8") )
    
    return jsonreply["updated"], jsonreply["products"]



def getUpdates(token, offset=0):
    """Query updates from telegram bot api
    
    
    Params:
        token (str):  authentication token for telegram bot api
        offset (int): number to tell telegram bot server, which messages are 
                      already been handled. To mark last message as handled, 
                      pass a number higher than the message's update_id. 
                      See https://core.telegram.org/bots/api#getupdates for more
                      information
    
    Returns:
        JSON file containing telegram bot api's response, 
        see https://core.telegram.org/bots/api#update for more information 
    
    """
    
    url = BOT_BASE_URL + token + "/getUpdates" #+ "/getUpdates?timeout=100"
    params = {'offset':offset}
    req = requests.get(url, data=params)
    
    return json.loads( req.content.decode("utf-8") )



def sendMessage(token, chatID, msg):
    """Send telegram message
    
    
    Params:
        token (str):  authentication token for telegram bot api
        chatID (int): identification number for chat to send reply to
        msg (str):    message to send with newline character at the end
        
    NOTE: Message is send in markdown mode, which produces monospace text. 
          It should start with ``` and end with ``` to achieve this effect.
        
    """
    url = BOT_BASE_URL + token + \
          "/sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(msg, chatID)
    
    if msg is not None:
        requests.get(url)

   
    
def convertStates(states):
    """Convert states requested from api into more descriptive form
    
    
    Params:
        states (dict):  dict containing states, e.g. {'jäätelö':False}
        
    Returns:
        states as dict, but descriptions as values instead of truth values    
    
    """

    statedict = {}

    for key in states:
        if states[key] == True:
            statedict[key] = "jäljellä"
        else:
            statedict[key] = "loppu"
            
    return statedict



def cmdFridge(token, chatID):
    """Handler for command "fridge"
    
    Queries states from castor fridge api and sends formatted status message 
    
    
    Params:
        See function "sendMessage"
        
    """
    
    unixTime = 0
    
    states = {}

    try:
        unixTime, states = getSwitchData()
    except:
        writeLog("errorneus reply")
    
    if unixTime == "":
        sendMessage(token, chatID, "`Ei dataa`")
        return
        
    lastUpdated = datetime.fromtimestamp(unixTime).strftime("%d.%m.%Y %H:%M:%S")
    states = convertStates(states)

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
    """Write log message to LOG_FILE with a timestamp
    
    
    Params:
        msg (str):         message to log
        addEndline (bool): whether to add "\n" to the end of the message 
    
    """

    with open(LOG_FILE, "a") as f:
        f.write("\n")
        f.write(msg)
        
        if addEndline == True:
            f.write("\n---------------------------------------------\n")
        


def main():
    
    with open("./.token", "r") as f:
        token = f.read().rstrip(" \n")
        
        
    updateID = 0
    result = {}


    while True:
    
        try:  
            result = getUpdates(token, updateID)
        
        except:
            writeLog("connection to telegram api failed")
            time.sleep(60)  # retry after 1 min
            continue
            
        
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

