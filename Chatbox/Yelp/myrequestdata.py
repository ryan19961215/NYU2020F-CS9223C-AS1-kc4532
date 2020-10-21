import requests
import time
import csv
import os

#www.nyctourist.com/manhattan-hotels.php
AREAS = ['Harlem, Manhattan','Morningside, Manhattan','Central Park','Chelsea, Manhattan','Clinton, Manhattan','East Harlem, Manhattan','Gramercy, Manhattan','Murray Hill, Manhattan', 'Greenwich Village, Manhattan','Soho, Manhattan','Lower Manhattan, Mahattan','Lower East Side, Manhattan','Upper East Side, Manhattan','Upper West Side, Manhattan','Inwood, Manhattan','Washington Heights, Manhattan','Midtown West, Manhattan','Midtown East, Manhattan','Time Squares, Manhatan','Garment, Manhattan','Stuyvesant Town, Manhattan','East Village, Manhattan','Little Italy, Manhattan','Tribeca, Manhattan','Financial District, Manhattan']

#www.ubereats.com/tw
CUISINES = ['Vegetable','Bubble Tea','Taiwanese','Japanese','American','Chinese','Korean','Pizza','Italian','Healthy','Thai','Vegitarian','Asian','Spaghetti','Chicken','Hong Kong','Dessert','Coffee','European','Hamburger','Mexican','French','German','Halal','Mediterrian','Indonesian','Belgian','Indian','Seafood','Malaysian']

#www.yelp.com/developers/documentations/v3/uthentication
HEADERS = {'Authorization': 'bearer j6hvNx9l3eyZweAbwNM6m695s6lsalF2MfQiPCcYQhCMvYsY3LNMt_4e4oO4UQVtsomzxwUyywZr8bUHhxVLFPkU-ksAqG6No2RXwkFuXKZR52-7RWRJRFgyhhiAX3Yx'}

#www.yelp.com/developers/documentation/v3/business
PARAMETERS = {
    'term': 'Chinese',
    'location': '',
    'radius': 3000,
    'limit': 50,
    'sort_by': 'distance'}

URL = 'https://api.yelp.com/v3/businesses/search'

CSV_FILE = 'yelp_data.csv'
AWS_DynanoDB_Key = 'restaurantID'
FORMHEAD = [AWS_DynanoDB_Key,'Name','Cuisine','Is Closed','Rating','Number of Reviews','Address','InsertTime']

AWS_DB_NAME = 'yelp-restaurants'
AWS_REGION = 'us-east-1'


def YelptoLocal():
    csv_all_data=[]
    i_total = len(AREAS) * len(CUISINES)
    for cuisine in CUISINES:
        PARAMETERS['term'] = cuisine
        for area in AREAS:
            PARAMETERS['location'] = area
            response = requests.get(URL , params=PARAMETERS , headers=HEADERS)
            page_data = response.json()['businesses']
            for data in page_data:
                localtime = time.asctime( time.localtime(time.time()) )
                item = {FORMHEAD[0]: data['id'],
                        FORMHEAD[1]: data['name'],
                        FORMHEAD[2]: cuisine,
                        FORMHEAD[3]: str(data['is_closed']),
                        FORMHEAD[4]: data['rating'],
                        FORMHEAD[5]: data['review_count'],
                        FORMHEAD[6]: data['location']['address1'],
                        FORMHEAD[7]: localtime}
                csv_all_data.append(item)
            #R = csv_all_data[6].copy()
            #csv_all_data.append(R)
            #R = csv_all_data[42].copy()
            #csv_all_data.append(R)
            #csv_all_data[50]['Cuisine'] = 'SPPSS'
            print('Finish', i ,'out of', i_total ,'process')
            
    # Cancel Duplicate
    print(type(csv_all_data))
    print('There are', len(csv_all_data) ,'in the data.')
    D = dict()
    kill = []
    for i,compare in enumerate(csv_all_data):
        #print('/')
        #print(D.get(compare[AWS_DynanoDB_Key]))
        #print(compare['Cuisine'])
        if D.get(compare[AWS_DynanoDB_Key]) is None or D.get(compare[AWS_DynanoDB_Key]) != compare['Cuisine']:
            D[compare[AWS_DynanoDB_Key]] = compare['Cuisine']
        else:
            kill.append(i)
    kill.reverse()
    for num in kill:
        del csv_all_data[num]
    print('There are', len(csv_all_data) ,'in the data.')
        
    # Record csv data
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
    with open(CSV_FILE, 'w', encoding='utf-8') as y:
        y_csv = csv.DictWriter(y, CSV_HEAD)
        y_csv.writeheader()
        y_csv.writerows(csv_all_data)
    return
 
import boto3
 
def LocaltoAws():
    # Upload csv data
    with open(CSV_FILE) as csvfile:
        rows = csv.reader(csvfile)
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        destination = dynamodb.Table(AWS_DB_NAME)
        for i,csv_row in enumerate(rows):
            if i == 0:
                title = csv_row
                continue
            item = dict()
            for j in range(len(title)):
                item[title[j]] = csv_row[j]
            destination.put_item(Item=item)
            print("Finish ",i," row")
            
   
def main():
    YelptoLocal()
    LocaltoAws()
    

if __name__=='__main__':
    main()
