from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

def save_document_to_db(uri, db_name, collection_name, document):
    client = pymongo.MongoClient(uri)
    db = client[db_name]
    collection = db[collection_name]
    result = collection.insert_one(document)
    return result.inserted_id