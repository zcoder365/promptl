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
DATABASE_NAME = "promptl"  # database name

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
            _db = _mongo_client[DATABASE_NAME]
            # Test the connection
            _mongo_client.admin.command('ping')
        
        return _db
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise

def add_story(title: str, story_content: str, prompts: dict, word_count: int, points_earned: int, username: str):
    """
    Add a new story to the database
    Args:
        title (str): Story title
        story_content (str): The actual story text
        prompts (dict): Writing prompts used
        word_count (int): Number of words in story
        points_earned (int): Points earned for this story
        username (str): Author's username
    Returns:
        str: Story ID if successful, None if failed
    """
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
            "author_username": username,
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
    """
    Get all stories written by a specific user
    Args:
        username (str): Username to get stories for
    Returns:
        list: List of story dictionaries, empty list if none found
    """
    try:
        # Get database connection
        db = get_db()
        stories_collection = db.stories
        
        # Query for user's stories, ordered by creation date (newest first)
        cursor = stories_collection.find(
            {"author_username": username}
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
    """
    Get all stories from the database
    Returns:
        list: List of all story dictionaries, empty list if none found
    """
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
    """
    Get a specific story by its ID
    Args:
        story_id (str): Story ID to retrieve
    Returns:
        dict: Story document if found, None if not found
    """
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
    """
    Delete a story (only if the user is the author)
    Args:
        story_id (str): Story ID to delete
        username (str): Username attempting to delete (for authorization)
    Returns:
        bool: True if successful, False if failed
    """
    try:
        # Get database connection
        db = get_db()
        stories_collection = db.stories
        
        # Delete only if the user is the author
        result = stories_collection.delete_one({
            "_id": ObjectId(story_id),
            "author_username": username
        })
        
        if result.deleted_count > 0:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error deleting story {story_id}: {e}")
        return False

def test_connection():
    """
    Test the database connection
    Returns:
        bool: True if connection successful, False otherwise
    """
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