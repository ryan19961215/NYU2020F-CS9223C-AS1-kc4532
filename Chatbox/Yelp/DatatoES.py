import csv
import os

csv_file_name = "yelp_data.csv"
#csv_file_name = "example.csv"
elastic_web = "https://search-restaurants-t7gyztz7emocvycpohpvgsxu34.us-east-1.es.amazonaws.com/restaurants/Restaurant/"


def csvreader():
    D = []
    with open(csv_file_name, newline='') as r:
        rows = csv.reader(r)
        for i,row in enumerate(rows):
            D.append([row[0],row[2]])
    return D

def command():
    cdata = csvreader()
    for i,data in enumerate(cdata):
        if i == 0:
            header = data
            continue
        command = "curl -XPUT -u AWSassignment1:@ws1sFUN! "+ elastic_web + str(i) + " -d '"+ "{" + '"{0}": "{1}", "{2}": "{3}"'.format(header[0],data[0],header[1],data[1]) + "}" +"' -H 'Content-Type: application/json'"
        os.system(command)
        print('\n')

if __name__=='__main__':
    command()

        
