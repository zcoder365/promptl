import sqlite3
from typing import Optional, List, Tuple
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Database file paths
USER_DATA_FILE = "data/users.db"
STORY_DATA_FILE = "data/stories.db"

# MongoDB connection details
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "promptl"
USERS_COLLECTION = "users"

# Database initialization functions
def get_db_connection(db_file: str) -> sqlite3.Connection:
    """Create a database connection with proper error handling."""
    try:
        return sqlite3.connect(db_file)
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database {db_file}: {e}")
        raise

def create_user_db():
    """Create users database if it doesn't exist."""
    try:
        conn = get_db_connection(USER_DATA_FILE)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                parent_email TEXT NOT NULL,
                streak INTEGER DEFAULT 0,
                points INTEGER DEFAULT 0
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error creating user database: {e}")
        raise
    finally:
        conn.close()

def create_stories_db():
    """Create stories database if it doesn't exist."""
    try:
        conn = get_db_connection(STORY_DATA_FILE)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                story_author TEXT NOT NULL,
                story_title TEXT NOT NULL,
                story_contents TEXT NOT NULL,
                story_word_count INTEGER NOT NULL,
                prompts TEXT NOT NULL,
                FOREIGN KEY (story_author) REFERENCES users(username)
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error creating stories database: {e}")
        raise
    finally:
        conn.close()

def create_databases():
    """Create both databases."""
    create_user_db()
    create_stories_db()

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