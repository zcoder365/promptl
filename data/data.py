import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import os

# MongoDB connection details
DATABASE_NAME = "promptl"
USERS_COLLECTION = "users"

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variables
MONGO_URI = os.getenv("MONGO_URI")

def get_mongo_client() -> MongoClient:
    """Create a MongoDB client with proper error handling."""
    try:
        client = MongoClient(MONGO_URI)
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        return client
    except ConnectionFailure as e:
        logging.error(f"Error connecting to MongoDB: {e}")
        raise

def login_user(username: str, password: str):
    """Log in a user using MongoDB."""
    try:
        client = get_mongo_client()
        db = client[DATABASE_NAME]
        users_collection = db[USERS_COLLECTION]
        user = users_collection.find_one({"username": username, "password": password})
        if user:
            logging.info(f"User {username} logged in successfully.")
            return user
        else:
            logging.warning(f"Login failed for user {username}. Incorrect username or password.")
            return None
    except Exception as e:
        logging.error(f"Error logging in user {username}: {e}")
        raise
    finally:
        client.close()