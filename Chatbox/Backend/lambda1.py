import datetime
import time
import os
import dateutil.parser
import boto3

from random import choice

MANHATTAN = ['harlem, manhattan','morningside, manhattan','central park, manhattan','Chelsea, manhattan','clinton, manhattan','east harlem, manhattan','gramercy, manhattan','murray hill, manhattan', 'greenwich village, manhattan','soho, manhattan','lower manhattan, mahattan','lower east side, manhattan','upper east side, manhattan','upper west side, manhattan','inwood, manhattan','washington heights, manhattan','midtown west, manhattan','midtown east, manhattan','time squares, manhatan','garment, manhattan','stuyvesant town, manhattan','east village, manhattan','little italy, manhattan','tribeca, manhattan','financial district, manhattan', 'manhattan']

CUISINE = ['vegetable','bubble tea','taiwanese','japanese','american','chinese','korean','pizza','italian','healthy','thai','vegitarian','asian','spaghetti','chicken','hong kong','dessert','coffee','european','hamburger','mexican','french','german','halal','mediterrian','indonesian','belgian','indian','seafood','malaysian']

queue_url = 'https://sqs.us-east-1.amazonaws.com/403382347655/2020nyucs9223c_as1_kc4532'

# --- Helpers that build all of the responses ---
def ResponseFormat_Invalid(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }

def ResponseFormat_Close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response

def ResponseFormat_Valid(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

def safe_int(n):
    if n is not None:
        return int(float(n))
    return n

def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False

def build_validation_result(isvalid, slot_to_elicit, message_content):
    return {
        'isValid': isvalid,
        'slotoElicit': slot_to_elicit,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def Validate(slots):
    location = slots['Location']
    cuisine = slots['Cuisine']
    people = safe_int(slots['People'])
    date = slots['Date']
    times = slots['Time']
    phone_number = slots['Telephone']

    print(('Slots: location={0}, cuisine={1}, people={2}, date={3}, time={4}, telephone={5}').format(location, cuisine, people, date, times, phone_number))

    if location is not None and not location.lower() in MANHATTAN:
        return build_validation_result(False,
                                       'Location',
                                       'We currently do not support {} as a valid destination or your answer is in the wrong format. Please enter a city area in Manhattan, using the format like "Soho, Manhattan". You can also try "Manhattan"'.format(location))
    if cuisine is not None and not cuisine.lower() in CUISINE:
        random_cuisine = choice(CUISINE)
        return build_validation_result(False,
                                       'Cuisine',
                                       'We currently do not support for {0} food. Do you want to have some {1} food instead? Type {2}. '.format(cuisine,random_cuisine,random_cuisine))
    if people is not None and (people < 1 or people > 15):
        return build_validation_result(
            False,
            'People',
            'You can make a reservations only from one to fifteen people.  How many people are there in your party?')
    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(
                False,
                'Date',
                'I did not understand your reservation date.  When would you like to reserve a table? You can try "Today".')
        if datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(
                False,
                'Date',
                'Are you saying about {}? Please choose a future date or "Today".'.format(date))
    if times is not None:
        if ':' not in times:
            return build_validation_result(
                False,
                'Time',
                'Sorry I dont understand this time, you should try to write in the format like 6:00 pm or 18:00.')
        hour, minute = times.split(':')
        hour = safe_int(hour)
        minute = safe_int(minute)
        if hour > 24 or minute > 60:
            return build_validation_result(
                False,
                'Time',
                'Sorry I dont understand this time, you should try to write in the format like 6:00 pm or 18:00.')
            
    if phone_number is not None:
        phone = str(phone_number.replace('-','').replace('+',''))
        if len(phone) < 7 or len(phone) > 12:
            return build_validation_result(
                False,
                'Telephone',
                'Please enter a 7 to 12 digit phone number')
    slot_list = [location,cuisine,people,date,times,phone_number]
    available_slot=len(list(filter(None,slot_list)))
    return build_validation_result(True, None, None)

def Lambda1toSQS(slots):
    print("[SQS]", slots)
    sqs = boto3.client('sqs')
    sqs.send_message(
        QueueUrl = queue_url,
        DelaySeconds=10,
        MessageAttributes = {
            'Location': {
                'DataType': 'String',
                'StringValue': slots['Location']},
            'Cuisine': {
                'DataType': 'String',
                'StringValue': slots['Cuisine']},
            'People': {
                'DataType': 'String',
                'StringValue': slots['People']},
            'Date': {
                'DataType': 'String',
                'StringValue': slots['Date']},
            'Time': {
                'DataType': 'String',
                'StringValue': slots['Time']},
            'Telephone': {
                'DataType': 'String',
                'StringValue': slots['Telephone']}
        }, MessageBody = ('Restauraunt Request'))
    return

def DiningSuggestHandler(intent_request):
    session_attributes = intent_request['sessionAttributes']
    confirmation = intent_request['currentIntent']['confirmationStatus']
    slots = intent_request['currentIntent']['slots']
    
    if confirmation == 'Confirmed':
        Lambda1toSQS(slots)

    if intent_request['invocationSource'] == 'DialogCodeHook':
        validation_result = Validate(intent_request['currentIntent']['slots'])
        # Fail on validating
        if not validation_result['isValid']:
            slots[validation_result['slotoElicit']] = None
            return ResponseFormat_Invalid(
                intent_request['sessionAttributes'],
                intent_request['currentIntent']['name'],
                slots,
                validation_result['slotoElicit'],
                validation_result['message']
            )
        # Success on validating
        return ResponseFormat_Valid(session_attributes, intent_request['currentIntent']['slots'])
    raise Exception('Lex Handling Rule Error')

def LexthroughLambda1(intent_request):
    print("INPUT: ", intent_request)
    print("TEXT: userId={}, intentName={}".format(intent_request['userId'], intent_request['currentIntent']['name']))
    intent_name = intent_request['currentIntent']['name']
    session_attributes = intent_request['sessionAttributes']
    
    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return DiningSuggestHandler(intent_request)
    elif intent_name == 'GreetingIntent':
        return ResponseFormat_Close(
            session_attributes,
            'Fulfilled',{
                'contentType': 'PlainText',
                'content': 'Hi there, how can I help?'
            }
        )
        
    elif intent_name == 'ThankYouIntent':
        return ResponseFormat_Close(
            session_attributes,
            'Fulfilled',{
                'contentType': 'PlainText',
                'content': 'You\'re welcome'
            }
        )
    raise Exception('Intent with name ' + intent_name + ' not supported')

def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    return LexthroughLambda1(event)
