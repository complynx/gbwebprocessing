import json
import sys
from pymongo import MongoClient

mongo_url = 'mongodb://localhost:27017/'
mongo_db = 'gbwebprocessing'
mongo_collection = 'jobs'

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} [input.json]")
        exit(1)

    with open(sys.argv[1], "r+") as fp:
        objects = json.load(fp)

    if not isinstance(objects, list):
        print(f"The contents of {sys.argv[1]} are not an array of objects as they need to be")
        exit(2)

    client = MongoClient(mongo_url)
    db = client[mongo_db]
    collection = db[mongo_collection]

    collection.insert_many(objects)
