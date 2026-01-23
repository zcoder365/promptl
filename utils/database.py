import os
from dotenv import load_dotenv
from datetime import datetime
import json
from pymongo import MongoClient
from bson.objectid import ObjectId

# Load the environment variables from the .env file
load_dotenv()

# Get MongoDB connection string from environment
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "Promptl"  # database name

# Global client variable
_mongo_client = None
_db = None

def get_db():
    """
    Get MongoDB database connection
    Returns:
        Database: MongoDB database instance
    """
    global _mongo_client, _db
    
    try:
        # Only create client once (singleton pattern)
        if _mongo_client is None:
            _mongo_client = MongoClient(MONGODB_URI)
            _db = _mongo_client["Promptl"]
            # Test the connection
            _mongo_client.admin.command('ping')
        
        return _db
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise

def add_story(title: str, story_content: str, prompts: dict, word_count: int, points_earned: int, username: str):
    try:
        # Validate input parameters
        if not title or not story_content or not username:
            return None
        
        # Get database connection
        db = get_db()
        stories_collection = db.stories
        
        # Create story document
        story_doc = {
            "title": title,
            "story": story_content,
            "prompts": prompts,  # MongoDB stores dicts natively as BSON
            "word_count": word_count,
            "points_earned": points_earned,
            "username": username,
            "created_at": datetime.now()
        }
        
        # Insert the story into MongoDB
        result = stories_collection.insert_one(story_doc)
        
        if result.inserted_id:
            story_id = str(result.inserted_id)  # Convert ObjectId to string
            return story_id
        else:
            return None
        
    except Exception as e:
        print(f"Error saving story: {e}")
        return None

def add_story_no_username(title: str, story_content: str, prompts: dict, word_count: int, points_earned: int):
    try:        
        # Get database connection
        db = get_db()
        stories_collection = db.stories
        
        # Create story document
        story_doc = {
            "title": title,
            "story": story_content,
            "prompts": prompts,  # MongoDB stores dicts natively as BSON
            "word_count": word_count,
            "points_earned": points_earned,
            "created_at": datetime.now()
        }
        
        # Insert the story into MongoDB
        result = stories_collection.insert_one(story_doc)
        
        if result.inserted_id:
            story_id = str(result.inserted_id)  # Convert ObjectId to string
            return story_id
        else:
            return None
        
    except Exception as e:
        print(f"Error saving story: {e}")
        return None

def get_user_stories(username: str):
    try:
        # Get database connection
        db = get_db()
        stories_collection = db.stories
        
        # Query for user's stories, ordered by creation date (newest first)
        cursor = stories_collection.find(
            {"username": username}
        ).sort("created_at", -1)  # -1 for descending order
        
        # Convert cursor to list of dicts
        stories_list = []
        for story in cursor:
            # Convert ObjectId to string for JSON serialization
            story['_id'] = str(story['_id'])
            stories_list.append(story)
        
        return stories_list
            
    except Exception as e:
        print(f"Error getting stories for {username}: {e}")
        return []

def get_all_stories():
    try:
        # Get database connection
        db = get_db()
        stories_collection = db.stories
        
        # Query for all stories, ordered by creation date (newest first)
        cursor = stories_collection.find().sort("created_at", -1)
        
        # Convert cursor to list of dicts
        stories_list = []
        for story in cursor:
            # Convert ObjectId to string for JSON serialization
            story['_id'] = str(story['_id'])
            stories_list.append(story)
        
        return stories_list
            
    except Exception as e:
        print(f"Error getting all stories: {e}")
        return []

def get_story_by_id(story_id: str):
    try:
        # Get database connection
        db = get_db()
        stories_collection = db.stories
        
        # Convert string ID to ObjectId
        story = stories_collection.find_one({"_id": ObjectId(story_id)})
        
        if story:
            # Convert ObjectId to string for JSON serialization
            story['_id'] = str(story['_id'])
            return story
        else:
            return None
            
    except Exception as e:
        print(f"Error getting story by ID {story_id}: {e}")
        return None

def delete_story(story_id: str, username: str):
    try:
        # Get database connection
        db = get_db()
        stories_collection = db.stories
        
        # Delete only if the user is the author
        result = stories_collection.delete_one({
            "_id": ObjectId(story_id),
            "username": username
        })
        
        if result.deleted_count > 0:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error deleting story {story_id}: {e}")
        return False

def add_user(username: str, password: str):
    user_document = {
        "username": username,
        "password": password
    }
    
    db = get_db()
    users_collection = db.users
    result = users_collection.insert_one(user_document)
    
    if result.inserted_id:
            user_id = str(result.inserted_id)  # Convert ObjectId to string
            return user_id
    else:
        return None

def find_user(username: str):
    db = get_db()
    users_collection = db.users
    
    result = users_collection.find_one({"username": username})
    
    if result is not None:
        return result
    else:
        print(f"Error getting user with username {username}.")
        return None

def test_connection():
    try:
        # Get database connection
        db = get_db()
        
        # Simple test query - count stories
        count = db.stories.count_documents({})
        
        print(f"MongoDB connection test successful. Found {count} stories")
        return True
        
    except Exception as e:
        print(f"MongoDB connection test failed: {e}")
        return False

def close_connection():
    """
    Close the MongoDB connection
    """
    global _mongo_client
    
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        print("MongoDB connection closed")