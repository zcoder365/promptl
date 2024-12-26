from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv() # load env vars from .env file
uri = os.getenv("MONGODB_URI") # get the uri from the env vars

# create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi("1"))

# send a ping to confirm a successful connection
try:
    client.admin.command("ping")
    print("Successfully connected to the server.")
except Exception as e:
    print(e)

def save_document_to_db(uri, db_name, collection_name, document):
    client = MongoClient(uri)
    db = client[db_name]
    collection = db[collection_name]
    result = collection.insert_one(document)
    return result.inserted_id