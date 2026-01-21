import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from datetime import datetime
import bcrypt
import logging
from postgrest.exceptions import APIError

# Set up logging for better debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load the environment variables from the .env file
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SERVICE_ROLE_KEY")  # Use service role key for full database access

# Debug: Check if environment variables are loaded correctly
logger.info(f"DEBUG - SUPABASE_URL: {SUPABASE_URL}")
logger.info(f"DEBUG - SERVICE_ROLE_KEY present: {bool(SUPABASE_KEY)}")
logger.info(f"DEBUG - SERVICE_ROLE_KEY length: {len(SUPABASE_KEY) if SUPABASE_KEY else 0}")

# Validate environment variables before creating client
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("SUPABASE_URL and SERVICE_ROLE_KEY must be set in .env file")
    logger.error("Please check your .env file exists and contains the correct variables")
    raise ValueError("SUPABASE_URL and SERVICE_ROLE_KEY must be set in .env file")

# Clean up URL if it has extra characters
SUPABASE_URL = SUPABASE_URL.strip()
SUPABASE_KEY = SUPABASE_KEY.strip()

if not SUPABASE_URL.startswith('https://'):
    logger.error(f"Invalid URL format: {SUPABASE_URL}")
    logger.error("SUPABASE_URL must start with 'https://' and should look like: https://your-project.supabase.co")
    raise ValueError("SUPABASE_URL must start with 'https://'")

# Initialize the supabase client
try:
    logger.info("Attempting to create Supabase client...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client created successfully")
except Exception as e:
    logger.error(f"Failed to create Supabase client: {e}")
    logger.error("Please verify your SUPABASE_URL and SERVICE_ROLE_KEY are correct")
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
        
        # Create user entry with hashed password
        new_user_entry = {
            "username": username,
            "password": hashed_password.decode('utf-8'),  # Store hash, not plain text
            "parent_email": "",
            "points": 0,
            "streak": 0  # Initialize streak field
        }
        
        # Insert into database with proper error handling
        logger.debug(f"Inserting user entry for: {username}")
        response = supabase.table("users").insert(new_user_entry).execute()
        
        # Check if the insertion was successful
        if response.data and len(response.data) > 0:
            logger.info(f"Successfully created user: {username}")
            return response.data[0]  # Return the created user data
        else:
            logger.error(f"Failed to create user: {username} - No data returned")
            return None
            
    except APIError as e:
        logger.error(f"Supabase API error adding user '{username}': {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error adding user '{username}': {e}")
        return None

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
    try:
        response = supabase.table("users").select("*").eq("username", username).execute()
        
        if response.data and len(response.data) > 0:
            user = response.data[0]
            logger.debug(f"Found user: {username}")
            return user
        else:
            logger.debug(f"User not found: {username}")
            return None  # Explicitly return None when user not found
            
    except APIError as e:
        logger.error(f"Supabase API error getting user {username}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting user {username}: {e}")
        return None

def update_user_points(username: str, points_to_add: int):
    """
    Update user's points by adding new points to current total
    Args:
        username (str): Username to update
        points_to_add (int): Points to add to current total
    Returns:
        bool: True if successful, False if failed
    """
    try:
        # First get current points
        current_user = get_user(username)
        if not current_user:
            logger.error(f"Cannot update points: User {username} not found")
            return False
            
        current_points = current_user.get('points', 0) or 0
        
        new_points = current_points + points_to_add
        
        # Update points
        response = supabase.table("users").update({
            "points": new_points
        }).eq("username", username).execute()
        
        if response.data:
            logger.info(f"User {username} points updated. New total: {new_points}")
            return True
        else:
            logger.error(f"Failed to update points for user {username}")
            return False
            
    except APIError as e:
        logger.error(f"Supabase API error updating points for {username}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating points for {username}: {e}")
        return False

def get_user_streak(username: str):
    """
    Get user's current streak count
    Args:
        username (str): Username to get streak for
    Returns:
        int: Current streak count, 0 if user not found or error
    """
    try:
        response = supabase.table("users").select("streak").eq("username", username).execute()
        
        if response.data and len(response.data) > 0:
            streak = response.data[0].get('streak', 0) or 0
            logger.debug(f"User {username} streak: {streak}")
            return streak
        else:
            logger.warning(f"Failed to get streak for user {username}")
            return 0
            
    except APIError as e:
        logger.error(f"Supabase API error getting streak for {username}: {e}")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error getting streak for {username}: {e}")
        return 0

def update_user_streak(username: str, streak: int):
    """
    Update user's streak count
    Args:
        username (str): Username to update
        streak (int): New streak value
    Returns:
        bool: True if successful, False if failed
    """
    try:
        response = supabase.table("users").update({"streak": streak}).eq("username", username).execute()
        
        if response.data:
            logger.info(f"User {username} streak updated to {streak}")
            return True
        else:
            logger.error(f"Failed to update streak for user {username}")
            return False
            
    except APIError as e:
        logger.error(f"Supabase API error updating streak for {username}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating streak for {username}: {e}")
        return False

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
        
        # Update password in database
        response = supabase.table("users").update({
            "password": hashed_new_password.decode('utf-8')
        }).eq("username", username).execute()
        
        if response.data:
            logger.info(f"Password updated successfully for user {username}")
            return True
        else:
            logger.error(f"Failed to update password for user {username}")
            return False
            
    except APIError as e:
        logger.error(f"Supabase API error updating password for {username}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating password for {username}: {e}")
        return False

def reset_user_password(username: str, new_password: str):
    """
    Reset user's password without requiring old password (for password resets)
    Args:
        username (str): Username to update
        new_password (str): New password to set
    Returns:
        bool: True if successful, False if failed
    """
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
        
        # Update password in database
        response = supabase.table("users").update({
            "password": hashed_new_password.decode('utf-8')
        }).eq("username", username).execute()
        
        if response.data:
            logger.info(f"Password reset successfully for user {username}")
            return True
        else:
            logger.error(f"Failed to reset password for user {username}")
            return False
            
    except APIError as e:
        logger.error(f"Supabase API error resetting password for {username}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error resetting password for {username}: {e}")
        return False

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
            logger.error("Missing required fields for story")
            return None
        
        logger.debug(f"Adding story '{title}' for user: {username}")
        logger.debug(f"Word count: {word_count}, Points: {points_earned}")
        
        # Check if supabase client is properly initialized
        if not supabase:
            logger.error("Supabase client not initialized")
            return None
            
        story_data = {
            "title": title,
            "story": story_content,
            "prompts": prompts,  # This will be stored as JSON in PostgreSQL
            "word_count": word_count,
            "points_earned": points_earned,
            "author_username": username,
            "created_at": datetime.now().isoformat()
        }
        
        # Insert the story into Supabase
        result = supabase.table('stories').insert(story_data).execute()
        
        # Check if the insert was successful
        if result.data and len(result.data) > 0:
            story_id = result.data[0]['id']
            logger.info(f"Story '{title}' saved successfully with ID: {story_id}")
            
            # Update user's points
            update_user_points(username, points_earned)
            
            return story_id
        else:
            logger.error("No data returned from story insert operation")
            return None
        
    except APIError as e:
        logger.error(f"Supabase API error saving story: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error saving story: {e}")
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
        response = supabase.table("stories").select("*").eq("author_username", username).order("created_at", desc=True).execute()
        
        if response.data:
            stories = response.data
            logger.info(f"Found {len(stories)} stories for user {username}")
            return stories
        else:
            logger.debug(f"No stories found for user {username}")
            return []
            
    except APIError as e:
        logger.error(f"Supabase API error getting stories for {username}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting stories for {username}: {e}")
        return []

def get_all_stories():
    """
    Get all stories from the database
    Returns:
        list: List of all story dictionaries, empty list if none found
    """
    try:
        response = supabase.table("stories").select("*").order("created_at", desc=True).execute()
        
        if response.data:
            stories = response.data
            logger.info(f"Retrieved {len(stories)} total stories")
            return stories
        else:
            logger.debug("No stories found in database")
            return []
            
    except APIError as e:
        logger.error(f"Supabase API error getting all stories: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting all stories: {e}")
        return []

def test_connection():
    """
    Test the Supabase connection
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        # Simple test query
        response = supabase.table("users").select("count", count="exact").execute()
        logger.info("Supabase connection test successful")
        return True
    except Exception as e:
        logger.error(f"Supabase connection test failed: {e}")
        return False