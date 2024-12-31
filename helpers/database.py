from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure, OperationFailure
import os
import hashlib
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# load environment vars
load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.uri = os.getenv("MONGODB_URI")
        self.db_name = "promptl"
        self.client = None
        
        # verify we have the necessary environment variables
        if not self.uri:
            raise ValueError("MongoDB URI not found in environment variables")
        
        # add connection timeout
        self.client_options = {
            "serverSelectionTimeoutMS": 5000,
            "connectTimeoutMS": 10000
        }
        
    def _get_connection(self) -> MongoClient:
        client = MongoClient(self.uri, server_api=ServerApi('1'))
        return client
    
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    # user management methods
    def add_user(self, username: str, password: str, email: str) -> bool:
        try:
            with self._get_connection() as client:
                db = client[self.db_name]
                
                # check if the user already exists
                if db.users.find_one({"username": username}):
                    return False
                
                # create a user document
                user_doc = {
                    "username": username,
                    "password": password,
                    "parent_email": email,
                    "points": 0,
                    "streak": 0
                }
                
                result = db.users.insert_one(user_doc)
                
                return bool(result.inserted_id)
        except Exception as e:
            self.logger.error(f"Error adding user {username}: {str(e)}")
            return False
        
        finally:
            client.close()
            
    def verify_login(self, username: str, password: str) -> bool:
        # create client connection
        client = self._get_connection()
        
        try:
            # get the database
            db = client[self.db_name]
            
            hashed_pw = self._hash_password(password)
            user = db.users.find_one({"username": username, "password": hashed_pw})
            
            return bool(user)
        
        except Exception as e:
            self.logger.error(f"Error verifying login for {username}: {str(e)}")
            return False
        
        finally:
            client.close()
    
    # story management methods
    def save_story(self, username: str, title: str, content: str, word_count: int, prompts: Dict[str, str]) -> bool:
        try:
            client = self._get_connection()
            db = client[self.db_name]
            
            story_doc = {
                "story_author": username,
                "title": title,
                "story": content,
                "story_word_count": word_count,
                "prompts": prompts
            }
            
            result = db.stories.insert_one(story_doc)
            return bool(result.inserted_id)
        
        except Exception as e:
            self.logger.error(f"Error saving story for {username}: {str(e)}")
            return False
        finally:
            client.close()
    
    def get_user_stories(self, username: str) -> List[Dict[str, Any]]:
        try:
            client = self._get_connection()
            db = client[self.db_name]
            
            stories = list(db.stories.find({"story_author": username}))
            return stories
            
        except Exception as e:
            self.logger.error(f"Error fetching stories for {username}: {str(e)}")
            return []
        finally:
            client.close()
    
    def update_user_stats(self, username: str, points: int = None, streak: int = None) -> bool:
        try:
            client = self._get_connection()
            db = client[self.db_name]
            
            update_fields = {}
            if points is not None:
                update_fields["points"] = points
            if streak is not None:
                update_fields["streak"] = streak
                
            if not update_fields:
                return True
                
            result = db.users.update_one(
                {"username": username},
                {"$set": update_fields}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            self.logger.error(f"Error updating stats for {username}: {str(e)}")
            return False
        finally:
            client.close()
    
    def get_total_word_count(self, username: str):
        db = self._get_connection()[self.db_name]
        
        result = db.stories.aggregate([
            {"$match": {"story_author": username}},
            {"$group":{
                "_id": None,
                "total_words": {"$sum": "$story_word_count"}
            }}
        ])
        
        agg_result = next(result, {"total_words": 0})
        return agg_result['total_words']
    
    def get_user_points(self, username: str) -> int:
        db = self._get_connection()[self.db_name]
        
        user = db.users.find_one(
            {"username": username},
            {"points": 1} # make sure the user has points
        )
        
        return user.get("points", 0) if user else 0
    
    def get_parent_email(self, username: str) -> Optional[str]:
        db = self._get_connection()[self.db_name]
        
        user = db.users.find_one(
            {"username": username},
            {"parent_email": 1} # there exists a parent email
        )
        
        return user.get("parent_email") if user else None
    
    def find_user(self, username: str) -> Optional[Dict]:
        # get the database connection
        db = self._get_connection()[self.db_name]
        
        # find the user by username
        user = db['users'].find_one({"username": username})
        
        # return the user
        return user

    def change_parent_email(self, new_email: str, username: str) -> bool:
        db = self._get_connection()[self.db_name]
        
        result = db.users.update_one(
            {"username": username},
            {"$set": {"parent_email": new_email}}
        )
        
        return result.modified_count > 0
    
    def find_story(self, story_id: str) -> Optional[Dict]:
        db = self._get_connection()[self.db_name]
        
        story = db.stories.find_one({"_id": story_id})
        return story

# create a single instance to be imported by other modules
db = DatabaseManager()