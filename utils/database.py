import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime
import bcrypt
import logging
import json

# Set up logging for better debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load the environment variables from the .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# Debug: Check if environment variable is loaded correctly
logger.info(f"DEBUG - DATABASE_URL present: {bool(DATABASE_URL)}")

# Validate environment variable before creating connection
if not DATABASE_URL:
    logger.error("DATABASE_URL must be set in .env file")
    logger.error("Please check your .env file exists and contains the correct variables")
    raise ValueError("DATABASE_URL must be set in .env file")

# Clean up URL if it has extra characters
DATABASE_URL = DATABASE_URL.strip()

# Helper function to get database connection
def get_db_connection():
    """
    Create and return a database connection
    Returns:
        connection: psycopg2 connection object with RealDictCursor
    """
    try:
        # psycopg2 can use the DATABASE_URL directly
        # RealDictCursor returns rows as dictionaries instead of tuples
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def add_user(username: str, password: str):
    """
    Add a new user to the database with hashed password
    Args:
        username (str): User's chosen username
        password (str): User's plain text password (will be hashed)
    Returns:
        dict: User data if successful, None if failed
    """
    conn = None
    cur = None
    try:
        # Validate inputs before database operation
        if not username or not password:
            logger.error("Username or password is empty")
            return None
            
        # Validate username format
        if len(username) < 3 or len(username) > 20:
            logger.error("Username must be between 3-20 characters")
            return None
            
        # Validate password strength
        if len(password) < 6:
            logger.error("Password must be at least 6 characters")
            return None
        
        logger.debug(f"Attempting to add user: {username}")
        
        # Hash the password before storing (SECURITY FIX)
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        # Connect to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert into database with proper error handling
        logger.debug(f"Inserting user entry for: {username}")
        cur.execute(
            """
            INSERT INTO users (username, password, parent_email, points, streak) 
            VALUES (%s, %s, %s, %s, %s) 
            RETURNING *
            """,
            (username, hashed_password.decode('utf-8'), "", 0, 0)
        )
        
        # Get the inserted user data
        new_user = cur.fetchone()
        conn.commit()  # commit the transaction
        
        if new_user:
            logger.info(f"Successfully created user: {username}")
            return dict(new_user)  # convert to regular dict
        else:
            logger.error(f"Failed to create user: {username} - No data returned")
            return None
            
    except psycopg2.Error as e:
        logger.error(f"Database error adding user '{username}': {e}")
        if conn:
            conn.rollback()  # rollback on error
        return None
    except Exception as e:
        logger.error(f"Unexpected error adding user '{username}': {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        # always close cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def authenticate_user(username: str, password: str):
    """
    Verify user credentials against stored hash
    Args:
        username (str): Username to authenticate
        password (str): Plain text password to verify
    Returns:
        dict: User data if authentication successful, None if failed
    """
    try:
        user = get_user(username)
        if not user:
            logger.warning(f"Authentication failed: User {username} not found")
            return None
            
        # Check password against stored hash
        stored_hash = user['password'].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            logger.info(f"Authentication successful for user: {username}")
            return user
        else:
            logger.warning(f"Authentication failed: Invalid password for user {username}")
            return None
            
    except Exception as e:
        logger.error(f"Authentication error for user {username}: {e}")
        return None
    
def get_user(username: str):
    """
    Retrieve user data by username
    Args:
        username (str): Username to search for
    Returns:
        dict: User data if found, None if not found
    """
    conn = None
    cur = None
    try:
        # Connect to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Query for user
        cur.execute(
            "SELECT * FROM users WHERE username = %s",
            (username,)
        )
        
        user = cur.fetchone()
        
        if user:
            logger.debug(f"Found user: {username}")
            return dict(user)  # convert to regular dict
        else:
            logger.debug(f"User not found: {username}")
            return None  # Explicitly return None when user not found
            
    except psycopg2.Error as e:
        logger.error(f"Database error getting user {username}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting user {username}: {e}")
        return None
    finally:
        # always close cursor and connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def update_user_points(username: str, points_to_add: int):
    """
    Update user's points by adding new points to current total
    Args:
        username (str): Username to update
        points_to_add (int): Points to add to current total
    Returns:
        bool: True if successful, False if failed
    """
    conn = None
    cur = None
    try:
        # First get current points
        current_user = get_user(username)
        if not current_user:
            logger.error(f"Cannot update points: User {username} not found")
            return False
            
        current_points = current_user.get('points', 0) or 0
        new_points = current_points + points_to_add
        
        # Connect to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Update points
        cur.execute(
            "UPDATE users SET points = %s WHERE username = %s RETURNING *",
            (new_points, username)
        )
        
        updated_user = cur.fetchone()
        conn.commit()
        
        if updated_user:
            logger.info(f"User {username} points updated. New total: {new_points}")
            return True
        else:
            logger.error(f"Failed to update points for user {username}")
            return False
            
    except psycopg2.Error as e:
        logger.error(f"Database error updating points for {username}: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating points for {username}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_user_streak(username: str):
    """
    Get user's current streak count
    Args:
        username (str): Username to get streak for
    Returns:
        int: Current streak count, 0 if user not found or error
    """
    conn = None
    cur = None
    try:
        # Connect to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Query for user's streak
        cur.execute(
            "SELECT streak FROM users WHERE username = %s",
            (username,)
        )
        
        result = cur.fetchone()
        
        if result:
            streak = result.get('streak', 0) or 0
            logger.debug(f"User {username} streak: {streak}")
            return streak
        else:
            logger.warning(f"Failed to get streak for user {username}")
            return 0
            
    except psycopg2.Error as e:
        logger.error(f"Database error getting streak for {username}: {e}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error getting streak for {username}: {e}")
        return 0
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def update_user_streak(username: str, streak: int):
    """
    Update user's streak count
    Args:
        username (str): Username to update
        streak (int): New streak value
    Returns:
        bool: True if successful, False if failed
    """
    conn = None
    cur = None
    try:
        # Connect to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Update streak
        cur.execute(
            "UPDATE users SET streak = %s WHERE username = %s RETURNING *",
            (streak, username)
        )
        
        updated_user = cur.fetchone()
        conn.commit()
        
        if updated_user:
            logger.info(f"User {username} streak updated to {streak}")
            return True
        else:
            logger.error(f"Failed to update streak for user {username}")
            return False
            
    except psycopg2.Error as e:
        logger.error(f"Database error updating streak for {username}: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating streak for {username}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def update_user_password(username: str, old_password: str, new_password: str):
    """
    Update user's password after verifying old password
    Args:
        username (str): Username to update
        old_password (str): Current password for verification
        new_password (str): New password to set
    Returns:
        bool: True if successful, False if failed
    """
    conn = None
    cur = None
    try:
        # First authenticate with old password
        user = authenticate_user(username, old_password)
        if not user:
            logger.warning(f"Password update failed: Invalid current password for {username}")
            return False
        
        # Validate new password
        if len(new_password) < 6:
            logger.error("New password must be at least 6 characters")
            return False
        
        # Hash new password
        salt = bcrypt.gensalt()
        hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)
        
        # Connect to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Update password in database
        cur.execute(
            "UPDATE users SET password = %s WHERE username = %s RETURNING *",
            (hashed_new_password.decode('utf-8'), username)
        )
        
        updated_user = cur.fetchone()
        conn.commit()
        
        if updated_user:
            logger.info(f"Password updated successfully for user {username}")
            return True
        else:
            logger.error(f"Failed to update password for user {username}")
            return False
            
    except psycopg2.Error as e:
        logger.error(f"Database error updating password for {username}: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating password for {username}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def reset_user_password(username: str, new_password: str):
    """
    Reset user's password without requiring old password (for password resets)
    Args:
        username (str): Username to update
        new_password (str): New password to set
    Returns:
        bool: True if successful, False if failed
    """
    conn = None
    cur = None
    try:
        # Check if user exists
        user = get_user(username)
        if not user:
            logger.error(f"Cannot reset password: User {username} not found")
            return False
        
        # Validate new password
        if len(new_password) < 6:
            logger.error("New password must be at least 6 characters")
            return False
        
        # Hash new password
        salt = bcrypt.gensalt()
        hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)
        
        # Connect to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Update password in database
        cur.execute(
            "UPDATE users SET password = %s WHERE username = %s RETURNING *",
            (hashed_new_password.decode('utf-8'), username)
        )
        
        updated_user = cur.fetchone()
        conn.commit()
        
        if updated_user:
            logger.info(f"Password reset successfully for user {username}")
            return True
        else:
            logger.error(f"Failed to reset password for user {username}")
            return False
            
    except psycopg2.Error as e:
        logger.error(f"Database error resetting password for {username}: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Unexpected error resetting password for {username}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

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
        int: Story ID if successful, None if failed
    """
    conn = None
    cur = None
    try:
        # Validate input parameters
        if not title or not story_content or not username:
            logger.error("Missing required fields for story")
            return None
        
        logger.debug(f"Adding story '{title}' for user: {username}")
        logger.debug(f"Word count: {word_count}, Points: {points_earned}")
        
        # Connect to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert the story into database
        # prompts dict will be converted to JSON automatically by psycopg2
        cur.execute(
            """
            INSERT INTO stories (title, story, prompts, word_count, points_earned, author_username, created_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s) 
            RETURNING id
            """,
            (title, story_content, json.dumps(prompts), word_count, points_earned, username, datetime.now())
        )
        
        result = cur.fetchone()
        conn.commit()
        
        if result:
            story_id = result['id']
            logger.info(f"Story '{title}' saved successfully with ID: {story_id}")
            
            # Update user's points
            update_user_points(username, points_earned)
            
            return story_id
        else:
            logger.error("No data returned from story insert operation")
            return None
        
    except psycopg2.Error as e:
        logger.error(f"Database error saving story: {e}")
        if conn:
            conn.rollback()
        return None
    except Exception as e:
        logger.error(f"Unexpected error saving story: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_user_stories(username: str):
    """
    Get all stories written by a specific user
    Args:
        username (str): Username to get stories for
    Returns:
        list: List of story dictionaries, empty list if none found
    """
    conn = None
    cur = None
    try:
        # Connect to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Query for user's stories, ordered by creation date (newest first)
        cur.execute(
            "SELECT * FROM stories WHERE author_username = %s ORDER BY created_at DESC",
            (username,)
        )
        
        stories = cur.fetchall()
        
        if stories:
            # Convert to list of dicts
            stories_list = [dict(story) for story in stories]
            logger.info(f"Found {len(stories_list)} stories for user {username}")
            return stories_list
        else:
            logger.debug(f"No stories found for user {username}")
            return []
            
    except psycopg2.Error as e:
        logger.error(f"Database error getting stories for {username}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting stories for {username}: {e}")
        return []
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def get_all_stories():
    """
    Get all stories from the database
    Returns:
        list: List of all story dictionaries, empty list if none found
    """
    conn = None
    cur = None
    try:
        # Connect to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Query for all stories, ordered by creation date (newest first)
        cur.execute("SELECT * FROM stories ORDER BY created_at DESC")
        
        stories = cur.fetchall()
        
        if stories:
            # Convert to list of dicts
            stories_list = [dict(story) for story in stories]
            logger.info(f"Retrieved {len(stories_list)} total stories")
            return stories_list
        else:
            logger.debug("No stories found in database")
            return []
            
    except psycopg2.Error as e:
        logger.error(f"Database error getting all stories: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting all stories: {e}")
        return []
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def test_connection():
    """
    Test the database connection
    Returns:
        bool: True if connection successful, False otherwise
    """
    conn = None
    cur = None
    try:
        # Connect to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Simple test query - count users
        cur.execute("SELECT COUNT(*) as count FROM users")
        result = cur.fetchone()
        
        logger.info(f"Database connection test successful. Found {result['count']} users")
        return True
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()