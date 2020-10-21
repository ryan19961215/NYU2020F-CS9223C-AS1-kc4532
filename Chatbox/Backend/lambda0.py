import json
import boto3
import time
import os

def lambda_handler(event, context):
    userid, text = get_info_from_request(event)
    if (userid is None) or (text is None):
        return get_response("Unable to get user ID or text.",-1)
    chatbot_text, userid = chatbot_response(userid, text)
    return get_response(chatbot_text, userid)
 
def chatbot_response(userid, text):
    client = boto3.client('lex-runtime')
    print("TEXT:",text)
    try:
        lex_response = client.post_text(botName ='Dining_Concierge_Chatbot', botAlias = '$LATEST', userId = str(userid), inputText = text, sessionAttributes={}, requestAttributes={},)
        print("LEX JSON:",lex_response)
        message = lex_response['message']
        print("RESPONSE:",message)
        return message , userid
    except Exception as exception:
        print("EXCEPT:", exception)
        return None , -2

def get_info_from_request(event):
    body = event
    print ("BODY:",body)
    if "messages" not in body:
        return -6 , 'lambda or API error, please come back later. Error number: 1'
    messages = event["messages"]
    if not isinstance(messages,list) or len(messages) < 1:
        return -4 , 'lambda or API error, please come back later. Error number: 2'
    message = messages[0]
    if "unstructured" not in message:
        return -5 , 'lambda or API error, please come back later. Error number: 3'
    if "text" not in message["unstructured"] or "id" not in message["unstructured"]:
        return -6 , 'lambda or API error, please come back later. Error number: 4'
    userid = message["unstructured"]["id"]
    text = message["unstructured"]["text"]
    return userid, text

def get_response(text,userid):
    body = {
        "messages":[
            {
                "type":"unstructured",
                "unstructured": {
                    "id": userid,
                    "text": text,
                    "time": time.time()
                }
            }]
    }
    response = {
        "status code": 200,
        "body": body
    }
    return response
        
