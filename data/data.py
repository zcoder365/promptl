import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# MongoDB connection details
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "promptl"
USERS_COLLECTION = "users"

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

def login_user(username: str, password: str) -> Optional[dict]:
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