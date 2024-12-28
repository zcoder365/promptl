from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
import hashlib
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

# Load environment variables
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

@contextmanager
def get_db_connection(uri: str):
    """
    Context manager for database connections to ensure proper resource management.
    
    Args:
        uri (str): MongoDB connection URI
    Yields:
        MongoClient: MongoDB client instance
    """
    client = None
    try:
        client = MongoClient(uri, server_api=ServerApi('1'))
        # Test connection
        client.admin.command('ping')
        yield client
    except Exception as e:
        raise DatabaseError(f"Database connection error: {str(e)}")
    finally:
        if client:
            client.close()

def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256.
    
    Args:
        password (str): Plain text password
    Returns:
        str: Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()

class MongoDBManager:
    def __init__(self, uri: str, db_name: str):
        self.uri = uri
        self.db_name = db_name

    def save_document(self, collection_name: str, document: Dict[str, Any]) -> str:
        """
        Save a document to specified collection.
        
        Args:
            collection_name (str): Name of the collection
            document (Dict[str, Any]): Document to save
        Returns:
            str: Inserted document ID
        """
        with get_db_connection(self.uri) as client:
            db = client[self.db_name]
            result = db[collection_name].insert_one(document)
            return str(result.inserted_id)

    def add_user(self, user_data: Dict[str, Any]) -> str:
        """
        Add a new user to the database with hashed password.
        
        Args:
            user_data (Dict[str, Any]): User data including username and password
        Returns:
            str: User ID
        """
        if 'password' in user_data:
            user_data['password'] = hash_password(user_data['password'])
        return self.save_document('users', user_data)

    def find_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Find user by username."""
        with get_db_connection(self.uri) as client:
            db = client[self.db_name]
            return db.users.find_one({"username": username})

    def login_user(self, username: str, password: str) -> bool:
        """
        Verify user login credentials using hashed password.
        """
        hashed_password = hash_password(password)
        with get_db_connection(self.uri) as client:
            db = client[self.db_name]
            result = db.users.find_one({
                "username": username,
                "password": hashed_password
            })
            return result is not None

    def update_user_field(self, username: str, field: str, value: Any) -> bool:
        """
        Generic method to update any user field.
        """
        with get_db_connection(self.uri) as client:
            db = client[self.db_name]
            result = db.users.update_one(
                {"username": username},
                {"$set": {field: value}}
            )
            return result.modified_count > 0

    def get_parent_email(self, username: str) -> Optional[str]:
        """Get parent email for a user."""
        with get_db_connection(self.uri) as client:
            db = client[self.db_name]
            result = db.users.find_one(
                {"username": username},
                {"parent_email": 1}
            )
            return result.get("parent_email") if result else None

    def get_user_points(self, username: str) -> int:
        """Get user points."""
        with get_db_connection(self.uri) as client:
            db = client[self.db_name]
            result = db.users.find_one(
                {"username": username},
                {"points": 1}
            )
            return result.get("points", 0) if result else 0

    def update_user_stats(self, username: str, points: Optional[int] = None,
                         streak: Optional[int] = None) -> bool:
        """
        Update user statistics (points and/or streak).
        """
        update_dict = {}
        if points is not None:
            update_dict["points"] = points
        if streak is not None:
            update_dict["streak"] = streak
            
        if not update_dict:
            return False
            
        with get_db_connection(self.uri) as client:
            db = client[self.db_name]
            result = db.users.update_one(
                {"username": username},
                {"$set": update_dict}
            )
            return result.modified_count > 0

    def add_story(self, story_data: Dict[str, Any]) -> str:
        """Add a new story."""
        return self.save_document('stories', story_data)

    def get_user_stories(self, username: str) -> List[Dict[str, Any]]:
        """Get all stories by a user."""
        with get_db_connection(self.uri) as client:
            db = client[self.db_name]
            return list(db.stories.find({"story_author": username}))

    def get_total_word_count(self, username: str) -> int:
        """Get total word count for a user's stories."""
        with get_db_connection(self.uri) as client:
            db = client[self.db_name]
            result = db.stories.aggregate([
                {"$match": {"story_author": username}},
                {"$group": {
                    "_id": None,
                    "total_word_count": {"$sum": "$story_word_count"}
                }}
            ])
            return next(result, {}).get("total_word_count", 0)