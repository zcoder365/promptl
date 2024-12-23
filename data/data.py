import sqlite3
from typing import Optional, List, Tuple
import logging

# Database file paths
USER_DATA_FILE = "data/users.db"
STORY_DATA_FILE = "data/stories.db"

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

# User account functions
def add_user_data(user_data: tuple):
    """Add a new user to the database."""
    try:
        conn = get_db_connection(USER_DATA_FILE)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (username, password, parent_email, streak, points) 
            VALUES (?, ?, ?, ?, ?)
        """, user_data)
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error adding user data: {e}")
        raise
    finally:
        conn.close()

def find_user(username: str) -> bool:
    """Check if a user exists in the database."""
    try:
        conn = get_db_connection(USER_DATA_FILE)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE username = ?", (username,))
        result = cur.fetchone()
        return result is not None
    except sqlite3.Error as e:
        logging.error(f"Error finding user: {e}")
        raise
    finally:
        conn.close()

def login_user(username: str, password: str) -> bool:
    """Verify user login credentials."""
    try:
        conn = get_db_connection(USER_DATA_FILE)
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM users WHERE username = ? AND password = ?", 
            (username, password)
        )
        result = cur.fetchone()
        return result is not None
    except sqlite3.Error as e:
        logging.error(f"Error during login: {e}")
        return False
    finally:
        conn.close()

# Parent email functions
def get_parent_email(username: str) -> Optional[str]:
    """Get a user's parent email."""
    try:
        conn = get_db_connection(USER_DATA_FILE)
        cur = conn.cursor()
        cur.execute(
            "SELECT parent_email FROM users WHERE username = ?",
            (username,)
        )
        result = cur.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        logging.error(f"Error getting parent email: {e}")
        return None
    finally:
        conn.close()

def change_parent_email(parent_email: str, username: str):
    """Update a user's parent email."""
    try:
        conn = get_db_connection(USER_DATA_FILE)
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET parent_email = ? WHERE username = ?",
            (parent_email, username)
        )
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error changing parent email: {e}")
        raise
    finally:
        conn.close()

# Points and streak functions
def get_user_points(username: str) -> int:
    """Get a user's points."""
    try:
        conn = get_db_connection(USER_DATA_FILE)
        cur = conn.cursor()
        cur.execute(
            "SELECT points FROM users WHERE username = ?",
            (username,)
        )
        result = cur.fetchone()
        return result[0] if result else 0
    except sqlite3.Error as e:
        logging.error(f"Error getting user points: {e}")
        return 0
    finally:
        conn.close()

def update_user_points(username: str, new_points: int):
    """Update a user's points."""
    try:
        conn = get_db_connection(USER_DATA_FILE)
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET points = ? WHERE username = ?",
            (new_points, username)
        )
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error updating user points: {e}")
        raise
    finally:
        conn.close()

def update_user_streak(username: str, new_streak: int):
    """Update a user's streak count."""
    try:
        conn = get_db_connection(USER_DATA_FILE)
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET streak = ? WHERE username = ?",
            (new_streak, username)
        )
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error updating user streak: {e}")
        raise
    finally:
        conn.close()

# Story functions
def add_story_data(story_data: tuple):
    """Add a new story to the database."""
    try:
        conn = get_db_connection(STORY_DATA_FILE)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO stories (story_author, story_title, story_contents, story_word_count, prompts) 
            VALUES (?, ?, ?, ?, ?)
        """, story_data)
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error adding story data: {e}")
        raise
    finally:
        conn.close()

def get_user_stories(username: str) -> List[Tuple]:
    """Get all stories by a user."""
    try:
        conn = get_db_connection(STORY_DATA_FILE)
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM stories WHERE story_author = ?", 
            (username,)
        )
        return cur.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Error getting user stories: {e}")
        return []
    finally:
        conn.close()

def find_story(story_title: str) -> Optional[Tuple]:
    """Find a story by its title."""
    try:
        conn = get_db_connection(STORY_DATA_FILE)
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM stories WHERE story_title = ?",
            (story_title,)
        )
        return cur.fetchone()
    except sqlite3.Error as e:
        logging.error(f"Error finding story: {e}")
        return None
    finally:
        conn.close()

def get_total_word_count(username: str) -> int:
    """Get total word count for a user's stories."""
    try:
        conn = get_db_connection(STORY_DATA_FILE)
        cur = conn.cursor()
        cur.execute("""
            SELECT SUM(story_word_count) 
            FROM stories 
            WHERE story_author = ?
        """, (username,))
        result = cur.fetchone()[0]
        return result if result is not None else 0
    except sqlite3.Error as e:
        logging.error(f"Error getting total word count: {e}")
        return 0
    finally:
        conn.close()

def get_user_streak(username: str) -> int:
    try:
        conn = get_db_connection(USER_DATA_FILE)
        cur = conn.cursor()
        cur.execute(
            "SELECT streak FROM users WHERE username = ?",
            (username,)
        )
        result = cur.fetchone()
        return result[0] if result else 0
    except sqlite3.Error as e:
        logging.error(f"Error getting user streak: {e}")
        return 0
    finally:
        conn.close()