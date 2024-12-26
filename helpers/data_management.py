from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "" # create env var for this

# create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi("1"))

def save_document_to_db(uri, db_name, collection_name, document):
    client = pymongo.MongoClient(uri)
    db = client[db_name]
    collection = db[collection_name]
    result = collection.insert_one(document)
    return result.inserted_id