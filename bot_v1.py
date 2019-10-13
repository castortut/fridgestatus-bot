import sys
import os
import json
import requests
from datetime import datetime

BOT_BASE_URL = "https://api.telegram.org/bot"
CASTOR_API_URL = "https://fridge0.api.avaruuskerho.fi/"

"""
Example reply from api:

{"updated": 1570918054.478339, "switches": [false, true, false, true, false, true]}
"""

# TODO: format message better
# TODO: improve switch-label-mapping
# TODO: error loggin in exception


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
    url = BOT_BASE_URL + token + "/sendMessage?text={}&chat_id={}".format(msg, chatID)
    
    if msg is not None:
        requests.get(url)

   
    
def formatStates(states):
    strings = []

    for state in states:

        if state == True:
            strings.append("jäljellä")
        else:
            strings.append("loppu")
            
    return strings



def main():
    
    with open("./.token", "r") as tokenFile:
        token = tokenFile.read().rstrip("\n")
        
    handledUpdates = []    

    while True: 
        result = getUpdates(token)
        
        if result["ok"] == False:
            errCode = result["error_code"]
            errDesc = result["description"]
            
            print("Error {}: {}".format(errCode, errDesc) )
            break

        
        data = result["result"]
        
        for i in range( 0, len(data) ):
            updateID = data[len(data)-1]["message"]["message_id"]
            
            if updateID in handledUpdates:
                continue
                
            if len(handledUpdates) > 1000:
                handledUpdates.clear()
                
            command = ""
            chatID = ""
            try:
                command = data[len(data)-1]["message"]["text"]
            
            except KeyError:
                msg = data[len(data)-1]
                print("key 'text' not found")
                print( json.dumps(msg, indent=4, sort_keys=True) )
                
            
            chatID = data[len(data)-1]["message"]["chat"]["id"]
            command = command.lstrip("/").replace("@CastorFridgeBot", " ").rstrip(" ").lower()

            if command == "fridge":
                lastUpdated, states = getSwitchData()

                lastUpdated = datetime.utcfromtimestamp(lastUpdated).strftime("%d.%m.%Y %H:%M:%S")
                states = formatStates(states)

                message = "limu:      {}\n" \
                          "pitsa:     {}\n" \
                          "<empty>:   {}\n" \
                          "<empty>:   {}\n" \
                          "<empty>:   {}\n" \
                          "<empty>:   {}\n\n" \
                          "päivitetty {}\n".format(states[0], 
                                                    states[1], 
                                                    states[2], 
                                                    states[3], 
                                                    states[4], 
                                                    states[5],
                                                    lastUpdated)
                          
                sendMessage(token, chatID, message)


            handledUpdates.append(updateID)
                
    
if __name__ == "__main__":
    main()

