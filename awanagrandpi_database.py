from pymongo import MongoClient
import json


# login data
with open("./config.json") as f:
    data = json.load(f)


client = MongoClient(f"mongodb+srv://{data['username']}:{data['password']}@ping.vzoyq.mongodb.net/awana_grand_pi?retryWrites=true&w=majority")

db = client.race_data

def insert_data(race_ID, racer, lane, time):
    race_data = {
        'raceid': race_ID,
        'racer': racer,
        'lane': lane,
        'time': time
    }

    result=db.reviews.insert_one(race_data)
    print(f"Created {result.inserted_id}")



