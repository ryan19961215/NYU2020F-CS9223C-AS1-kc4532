import boto3
import time
 
def Lambda0throughLex(userid, usertext):
    client = boto3.client('lex-runtime')
    print("TEXT:",usertext)
    try:
        lex_response = client.post_text(
            botName ='Dining_Concierge_Chatbot',
            botAlias = '$LATEST',
            userId = str(userid),
            inputText = usertext,
            sessionAttributes={},
            requestAttributes={},
        )
        print("LEXRESPONSE_ORI:",lex_response)
        servertext = lex_response['message']
        print("LEXRESPONSE_TRE:", servertext)
        return userid, servertext
    except Exception as exception:
        print("EXCEPT:", exception)
        return -5, 'lambda or API error, please come back later. Error number: 5'

def APItoLambda0(event):
    body = event
    print ("APIMESSAGE_ORI:",body)
    if "messages" not in body:
        return -1 , 'API error. Error number: 1'
    messages = event["messages"]
    if not isinstance(messages,list) or len(messages) < 1:
        return -2 , 'JS error. Error number: 2'
    message = messages[0]
    if "unstructured" not in message:
        return -3 , 'JS or API error. Error number: 3'
    if "text" not in message["unstructured"] or "id" not in message["unstructured"]:
        return -4 , 'JS or API error. Error number: 4'
    userid = message["unstructured"]["id"]
    text = message["unstructured"]["text"]
    return userid, text

def ResponseFormat(userid, text):
    response = {
        "status code": 200,
        "body": {
            "messages":[{
                "type":"unstructured",
                "unstructured": {
                    "id": userid,
                    "text": text,
                    "time": time.time()
                }
            }]
        }
    }
    return response

def lambda_handler(event, context):
    userid, usertext = APItoLambda0(event)
    if (userid is None) or (usertext is None):
        return ResponseFormat(-6 , "Unable to get user ID or text.")
    userid, servertext = Lambda0throughLex(userid, usertext)
    return ResponseFormat(userid, servertext)
