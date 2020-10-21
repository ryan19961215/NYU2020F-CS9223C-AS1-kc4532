import urllib3
import json
import time
import boto3
import time

from random import sample

beta = True
ACCPASS = 'AWSassignment1:@ws1sFUN!'
RECOMMEND_NUM = 3
COUNTRY = '886'

# SQS to Lambda
def sqstolambda2():
    sqs = boto3.client('sqs',region_name="us-east-1")
    sqs_url = 'https://sqs.us-east-1.amazonaws.com/403382347655/2020nyucs9223c_as1_kc4532'
    # Get receive information
    input_info = sqs.receive_message(QueueUrl = sqs_url, AttributeNames=['SentTimestamp'], MessageAttributeNames=['All'], VisibilityTimeout=0, WaitTimeSeconds=0)
    RETRY = 2
    for i in range(RETRY):
        if 'Messages' in input_info:
            break
        if i==(RETRY-1):
            return None
        print('[INFO]',input_info)
        input_info = sqs.receive_message(QueueUrl = sqs_url, AttributeNames=['SentTimestamp'], MessageAttributeNames=['All'], VisibilityTimeout=0, WaitTimeSeconds=0)
        print("RETRY: Fail on getting data")
        time.sleep(1)
    decode_half = input_info['Messages'][0]['MessageAttributes']
    decode_message = {}
    index = list(decode_half.keys())
    for prop in index:
        decode_message[prop]=decode_half[prop]['StringValue']
    print("[CLIENT REQUEST] ",decode_message)
    if not beta:
        sqs.delete_message(QueueUrl = sqs_url, ReceiptHandle = input_info['Messages'][0]['ReceiptHandle'])
    return decode_message

# Lambda thorohgh ES
def lambda2throughES(decode_message):
    es_url = 'https://search-restaurants-t7gyztz7emocvycpohpvgsxu34.us-east-1.es.amazonaws.com/restaurants/_search?'
    #es_url = 'https://search-cs9223cas1-kc4532-iam-7zp4wbmubju5uqxntdmqvzloge.us-east-1.es.amazonaws.comrestaurants/_search?'
    headers = {"Content-Type": "application/json"}
    http = urllib3.PoolManager()
    auth_headers = urllib3.make_headers(basic_auth=ACCPASS)
    full_es_url = es_url+"q={}".format(decode_message['Cuisine'])
    es_response = http.request("GET", full_es_url,headers=auth_headers)
    es_decode = json.loads(es_response.data.decode('utf-8'))
    es_decode = es_decode['hits']['hits']
    restaurantIDs = []
    for restaurant in es_decode:
        restaurantIDs.append(restaurant['_source']['restaurantID'])
    print("[ES RECOMMENDATION] ",restaurantIDs)
    return restaurantIDs

# Lambda thorohgh DynamoDB
def lambda2throughDynamoDB(restaurantIDs, decode_message):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('yelp-restaurants')

    # Set text message
    hello = 'Hello! Here are my '+decode_message['Cuisine']+' restaurants suggestions for '+decode_message['People']+' people, for '+decode_message['Date']+' at '+decode_message['Time']+':\n'

    context = ''
    ids = sample(restaurantIDs, k=RECOMMEND_NUM)
    for i,id in enumerate(ids):
        item = table.get_item(Key = {"restaurantID": id})
        context += str(i+1)+'. '+item['Item']['Name']+', located at '+item['Item']['Address']+'\n'
    context += 'Enjoy your meal!'
    sns_message = hello+context
    print("[SNS] ",sns_message)

    return sns_message


# Lambda to SNS
def lambda2toSNS(decode_message, sns_message):
    sns = boto3.client("sns", region_name="us-east-1")
    phonenumber = COUNTRY + decode_message['Telephone']
    sns.publish(PhoneNumber=phonenumber, Message=sns_message)
    VictoryScreech = "Recommndation has Send to "+ phonenumber
    print("[FINISH] ",VictoryScreech )
    return VictoryScreech

# Main
def lambda_handler(event, context):
    decode_message = sqstolambda2()
    if decode_message is None:
        return {
            'statusCode': 200,
            'body': json.dumps('No data or server is busy now. Please try again.')
        }
    restaurantIDs = lambda2throughES(decode_message)
    sns_message = lambda2throughDynamoDB(restaurantIDs, decode_message)
    VictoryScreech = lambda2toSNS(decode_message, sns_message)
    
    return {
        'statusCode': 200,
        'body': json.dumps(VictoryScreech)
    }



