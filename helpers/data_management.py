from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

# load .env file and get the uri
load_dotenv()
uri = os.getenv("MONGODB_URI")

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

# user account functions
def add_user_data(uri, db_name, user_data: dict):
    """Add a new user to the database."""
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db["users"]
        result = collection.insert_one(user_data)
        return result.inserted_id
    except Exception as e:
        print(f"Error adding user data: {e}")
        raise

def find_user(uri, db_name, username: str) -> bool:
    """Check if a user exists in the database."""
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db["users"]
        result = collection.find_one({"username": username})
        return result is not None
    except Exception as e:
        print(f"Error finding user: {e}")
        raise

def login_user(uri, db_name, username: str, password: str) -> bool:
    """Verify user login credentials."""
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db["users"]
        result = collection.find_one({"username": username, "password": password})
        return result is not None
    except Exception as e:
        print(f"Error during login: {e}")
        return False

# Parent email functions
def get_parent_email(uri, db_name, username: str):
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db["users"]
        result = collection.find_one({"username": username}, {"parent_email": 1})
        return result["parent_email"] if result else None
    except Exception as e:
        print(f"Error getting parent email: {e}")
        return None

def change_parent_email(uri, db_name, parent_email: str, username: str):
    """Update a user's parent email."""
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db["users"]
        result = collection.update_one({"username": username}, {"set": {"parent_email": parent_email}})
        return result.modified_count
    except Exception as e:
        print(f"Error changing parent email: {e}")
        raise

# Points and streak functions
def get_user_points(uri, db_name, username: str) -> int:
    """Get a user's points."""
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db["users"]
        result = collection.find_one({"username": username}, {"points": 1})
        return result["points"] if result else 0
    except Exception as e:
        print(f"Error getting user points: {e}")
        return 0

def update_user_points(uri, db_name, username: str, new_points: int):
    """Update a user's points."""
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db["users"]
        result = collection.update_one({"username": username}, {"$set": {"points": new_points}})
        return result.modified_count
    except Exception as e:
        print(f"Error updating user points: {e}")
        raise

def update_user_streak(uri, db_name, username: str, new_streak: int):
    """Update a user's streak count."""
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db["users"]
        result = collection.update_one({"username": username}, {"$set": {"streak": new_streak}})
        return result.modified_count
    except Exception as e:
        print(f"Error updating user streak: {e}")
        raise

# STORY FUNCTIONS
def add_story_data(uri, db_name, story_data: dict):
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db["stories"]
        result = collection.insert_one(story_data)
        return result.inserted_id
    except Exception as e:
        print(f"Error adding story data: {e}")
        raise

def get_user_stories(uri, db_name, username: str) -> List[dict]:
    """Get all stories by a user."""
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db["stories"]
        result = collection.find({"story_author": username})
        return list(result)
    except Exception as e:
        print(f"Error getting user stories: {e}")
        return []

def find_story(uri, db_name, story_title: str) -> Optional[dict]:
    """Find a story by its title."""
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db["stories"]
        result = collection.find_one({"story_title": story_title})
        return result
    except Exception as e:
        print(f"Error finding story: {e}")
        return None

def get_total_word_count(uri, db_name, username: str) -> int:
    """Get total word count for a user's stories."""
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db["stories"]
        result = collection.aggregate([
            {"$match": {"story_author": username}},
            {"$group": {"_id": None, "total_word_count": {"$sum": "$story_word_count"}}}
        ])
        total_word_count = next(result, {}).get("total_word_count", 0)
        return total_word_count
    except Exception as e:
        print(f"Error getting total word count: {e}")
        return 0

def get_user_streak(uri, db_name, username: str) -> int:
    try:
        client = MongoClient(uri)
        db = client[db_name]
        collection = db["users"]
        result = collection.find_one({"username": username}, {"streak": 1})
        return result["streak"] if result else 0
    except Exception as e:
        print(f"Error getting user streak: {e}")
        return 0
