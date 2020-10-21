# Modified from AWS example code
import json
import datetime
import time
import os
import dateutil.parser
import logging
import boto3

from random import choice

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

MANHATTAN = ['harlem, manhattan','morningside, manhattan','central park, manhattan','Chelsea, manhattan','clinton, manhattan','east harlem, manhattan','gramercy, manhattan','murray hill, manhattan', 'greenwich village, manhattan','soho, manhattan','lower manhattan, mahattan','lower east side, manhattan','upper east side, manhattan','upper west side, manhattan','inwood, manhattan','washington heights, manhattan','midtown west, manhattan','midtown east, manhattan','time squares, manhatan','garment, manhattan','stuyvesant town, manhattan','east village, manhattan','little italy, manhattan','tribeca, manhattan','financial district, manhattan', 'manhattan']

CUISINE = ['vegetable','bubble tea','taiwanese','japanese','american','chinese','korean','pizza','italian','healthy','thai','vegitarian','asian','spaghetti','chicken','hong kong','dessert','coffee','european','hamburger','mexican','french','german','halal','mediterrian','indonesian','belgian','indian','seafood','malaysian']

queue_url = 'https://sqs.us-east-1.amazonaws.com/403382347655/2020nyucs9223c_as1_kc4532'

# --- Helpers that build all of the responses ---
def invalid_respond(session_attributes, intent_name, slots, slot_to_elicit, message):
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

def close_intend_respond(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response

def valid_respond(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# --- Helper Functions ---
def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(float(n))
    return n


def try_ex(func):
    try:
        return func()
    except KeyError:
        return None

def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


##
def validate(slots):
    location = try_ex(lambda: slots['Location'])
    cuisine = try_ex(lambda: slots['Cuisine'])
    people = safe_int(try_ex(lambda: slots['People']))
    date = try_ex(lambda: slots['Date'])
    time = try_ex(lambda: slots['Time'])
    phone_number = try_ex(lambda: slots['Telephone'])

    logger.debug(('dispatch location={}, cuisine={}, people={}, date={}, time={}, telephone={}').format(location, cuisine, people, date, time, phone_number))

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
            'You can make a reservations only from one to fifteen people.  How many people are there in your party?'
        )
        
    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'Date', 'I did not understand your reservation date.  When would you like to reserve a table? You can try "Today".')
        if datetime.datetime.strptime(date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'Date', 'Are you saying about {}? Please choose a future date or "Today".'.format(date))
    
    if time is not None:
        hour, minute = time.split(':')
        hour = safe_int(hour)
        minute = safe_int(minute)
        if hour > 24 or minute > 60:
            return build_validation_result(False, 'Time', 'Sorry I dont understand this time, you should try to write in the format like 6am or 18:00.')
            
    if phone_number is not None:
        phone = str(phone_number.replace('-','').replace('+',''))
        if len(phone) < 7 or len(phone) > 12:
            return build_validation_result(False, 'Telephone', 'Please enter a 7 to 12 digit phone number')

    return build_validation_result(True, None, None)

def send_sqs(slots):
    print("[SQS]", slots)
    sqs = boto3.client('sqs')
    sqs.send_message(QueueUrl = queue_url,DelaySeconds=10,
        MessageAttributes = {
            'Location': {
                'DataType': 'String',
                'StringValue': slots['Location']
            },
            'Cuisine': {
                'DataType': 'String',
                'StringValue': slots['Cuisine']
            },
            'People': {
                'DataType': 'String',
                'StringValue': slots['People']
            },
            'Date': {
                'DataType': 'String',
                'StringValue': slots['Date']
            },
            'Time': {
                'DataType': 'String',
                'StringValue': slots['Time']
            },
            'Telephone': {
                'DataType': 'String',
                'StringValue': slots['Telephone']
            }
        }, MessageBody = ('Restauraunt Request'))
    return


def dining_suggest(intent_request):
    location = try_ex(lambda: intent_request['currentIntent']['slots']['Location'])
    cuisine = try_ex(lambda: intent_request['currentIntent']['slots']['Cuisine'])
    people = safe_int(try_ex(lambda: intent_request['currentIntent']['slots']['People']))
    date = try_ex(lambda: intent_request['currentIntent']['slots']['Date'])
    time = try_ex(lambda: intent_request['currentIntent']['slots']['Time'])
    telephone = try_ex(lambda: intent_request['currentIntent']['slots']['Telephone'])
    
    session_attributes = intent_request['sessionAttributes']
    confirmation = intent_request['currentIntent']['confirmationStatus']

    # Load confirmation history and track the current reservation.
    reservation = json.dumps({
        'ReservationType': 'Dining',
        'Location': location,
        'Cuisine': cuisine,
        'People': people,
        'Date': date,
        'Time': time,
        'Telephone': telephone
    })
    session_attributes['currentReservation'] = reservation
    
    if confirmation == 'Confirmed':
        sqs_slots = intent_request['currentIntent']['slots']
        send_sqs(sqs_slots)

    if intent_request['invocationSource'] == 'DialogCodeHook':
        validation_result = validate(intent_request['currentIntent']['slots'])
        if not validation_result['isValid']: #Invalid intent
            slots = intent_request['currentIntent']['slots']
            slots[validation_result['violatedSlot']] = None

            return invalid_respond(
                intent_request['sessionAttributes'],
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )

        return valid_respond(session_attributes, intent_request['currentIntent']['slots'])
    else:
        logger.error("InvocationSource Wrong")



# --- Intents ---
def dispatch(intent_request):
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']
    session_attributes = intent_request['sessionAttributes']
    
    print("[EVENT]:", intent_request)
    
    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return dining_suggest(intent_request)
        
    elif intent_name == 'GreetingIntent':
        return close_intend_respond(
            session_attributes,'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': 'Hi there, how can I help?'
            }
        )
        
    elif intent_name == 'ThankYouIntent':
        return close_intend_respond(
            session_attributes,'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': 'You\'re welcome'
            }
        )

    raise Exception('Intent with name ' + intent_name + ' not supported')


# --- Main handler ---
def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)

