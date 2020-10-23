import urllib3
import json
import time
import boto3
import time

from random import sample

beta = False
ACCPASS = 'AWSassignment1:@ws1sFUN!'
RECOMMEND_NUM = 3

# SQS to Lambda
def SQStoLambda2():
    sqs = boto3.client('sqs',region_name="us-east-1")
    sqs_url = 'https://sqs.us-east-1.amazonaws.com/403382347655/2020nyucs9223c_as1_kc4532'
    # Get receive information
    input_info = sqs.receive_message(QueueUrl = sqs_url, AttributeNames=['SentTimestamp'], MessageAttributeNames=['All'], VisibilityTimeout=0, WaitTimeSeconds=0)
    RETRY = 2
    for i in range(RETRY):
        print('SQS message:',input_info)
        if 'Messages' in input_info:
            break
        if i==(RETRY-1):
            return None
        input_info = sqs.receive_message(QueueUrl = sqs_url, AttributeNames=['SentTimestamp'], MessageAttributeNames=['All'], VisibilityTimeout=0, WaitTimeSeconds=0)
        print("RETRY: Fail on getting data")
        time.sleep(1)
    decode_half = input_info['Messages'][0]['MessageAttributes']
    Decode_Message = {}
    index = list(decode_half.keys())
    for prop in index:
        Decode_Message[prop]=decode_half[prop]['StringValue']
    print("CLIENT REQUEST:",Decode_Message)
    if not beta:
        sqs.delete_message(QueueUrl = sqs_url, ReceiptHandle = input_info['Messages'][0]['ReceiptHandle'])
    return Decode_Message

# Lambda thorohgh ES
def Lambda2throughES(Decode_Message):
    es_url = 'https://search-restaurants-t7gyztz7emocvycpohpvgsxu34.us-east-1.es.amazonaws.com/restaurants/_search?'
    #es_url = 'https://search-cs9223cas1-kc4532-iam-7zp4wbmubju5uqxntdmqvzloge.us-east-1.es.amazonaws.comrestaurants/_search?'
    headers = {"Content-Type": "application/json"}
    http = urllib3.PoolManager()
    auth_headers = urllib3.make_headers(basic_auth=ACCPASS)
    full_es_url = es_url+"q={}".format(Decode_Message['Cuisine'])
    es_response = http.request("GET", full_es_url,headers=auth_headers)
    es_decode = json.loads(es_response.data.decode('utf-8'))
    es_decode = es_decode['hits']['hits']
    RestaurantIDs = []
    for restaurant in es_decode:
        RestaurantIDs.append(restaurant['_source']['restaurantID'])
    print("ES recommendation:",RestaurantIDs)
    return RestaurantIDs

# Lambda thorohgh DynamoDB
def Lambda2throughDynamoDB(RestaurantIDs, Decode_Message):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('yelp-restaurants')

    # Set text message
    hello = 'Hello! Here are my '+Decode_Message['Cuisine']+' restaurants suggestions for '+Decode_Message['People']+' people, for '+Decode_Message['Date']+' at '+Decode_Message['Time']+':\n'
    context = ''
    ids = sample(RestaurantIDs, k=RECOMMEND_NUM)
    for i,id in enumerate(ids):
        item = table.get_item(Key = {"restaurantID": id})
        context += str(i+1)+'. '+item['Item']['Name']+', located at '+item['Item']['Address']+'\n'
    context += 'Enjoy your meal!'
    SNS_Message = hello+context
    print("SNS message:",SNS_Message)

    return SNS_Message


# Lambda to SNS
def Lambda2toSNS(Decode_Message, SNS_Message):
    sns = boto3.client("sns", region_name="us-east-1")
    phonenumber = Decode_Message['Telephone']
    sns.publish(PhoneNumber=phonenumber, Message=SNS_Message)
    VictoryScreech = "Recommndation has Send to "+ phonenumber
    print("[FINISH] ",VictoryScreech )
    return VictoryScreech

# Main
def lambda_handler(event, context):
    Decode_Message = SQStoLambda2()
    if Decode_Message is None:
        return {
            'statusCode': 200,
            'body': json.dumps('No data or server is busy now. Please try it later.')
        }
    RestaurantIDs = Lambda2throughES(Decode_Message)
    SNS_Message = Lambda2throughDynamoDB(RestaurantIDs, Decode_Message)
    VictoryScreech = Lambda2toSNS(Decode_Message, SNS_Message)
    
    return {
        'statusCode': 200,
        'body': json.dumps(VictoryScreech)
    }



