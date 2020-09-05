import sys
from pymongo import MongoClient

mongo_url = 'mongodb://localhost:27017/'
mongo_db = 'gbwebprocessing'
mongo_collection = 'jobs'

if __name__ == "__main__":
    use_upper = False
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} [-U] salary_threshold")
        exit(1)

    if len(sys.argv) > 2 and sys.argv[1] == "-U":
        use_upper = True

    client = MongoClient(mongo_url)
    db = client[mongo_db]
    collection = db[mongo_collection]

    field = "salary_upper" if use_upper else "salary_lower"

    from pprint import pprint
    for doc in collection.find({field: { "$gt": int(sys.argv[-1])}}):
        pprint(doc)
