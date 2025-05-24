from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime

# load the environment variables from the .env file
load_dotenv() # load the file
SUPABASE_URL = os.getenv("SUPABASE_URL") # get the database uri
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") # get the database key

# initialize the supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_user(username: str, password: str):
    try:
        # Note: password should already be hashed when passed to this function
        new_user_entry = {
            "username": username,
            "password": password  # Already hashed by main.py
        }
        
        response = supabase.table("users").insert(new_user_entry).execute()
        return response.data
        
    except Exception as e:
        print(f"Error adding user: {e}")
        return None
    
def get_user(username: str):
    try:
        response = supabase.table("users").select("*").eq("username", username).execute()
        
        if response.data and len(response.data) > 0:
            user = response.data[0]
            print(f"Debug - User structure: {user.keys()}")
            return user
        else:
            return None  # Explicitly return None when user not found
            
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def update_user_points(username: str, points_to_add: int):
    """Update user's total points by adding new points"""
    try:
        # First get current points
        current_user = get_user(username)
        if not current_user:
            print(f"User {username} not found")
            return False
            
        current_points = current_user.get('points', 0) or 0
        new_total_points = current_points + points_to_add
        
        # Update the user's points
        response = supabase.table("users").update({"points": new_total_points}).eq("username", username).execute()
        
        if response.data:
            print(f"User {username} points updated successfully. New total: {new_total_points}")
            return True
        else:
            print(f"Failed to update points for user {username}.")
            return False
            
    except Exception as e:
        print(f"Error updating user points: {e}")
        return False

def update_user_word_count(username: str, word_count_to_add: int):
    """Update user's total word count by adding new words"""
    try:
        # First get current word count
        current_user = get_user(username)
        if not current_user:
            print(f"User {username} not found")
            return False
            
        current_word_count = current_user.get('total_word_count', 0) or 0
        new_total_words = current_word_count + word_count_to_add
        
        # Update the user's word count
        response = supabase.table("users").update({"total_word_count": new_total_words}).eq("username", username).execute()
        
        if response.data:
            print(f"User {username} word count updated successfully. New total: {new_total_words}")
            return True
        else:
            print(f"Failed to update word count for user {username}.")
            return False
            
    except Exception as e:
        print(f"Error updating user word count: {e}")
        return False

def get_user_streak(username: str):
    try:
        # Get the user's streak
        response = supabase.table("users").select("streak").eq("username", username).execute()
        
        if response.data and len(response.data) > 0:
            streak = response.data[0].get('streak', 0) or 0
            print(f"User {username} streak: {streak}")
            return streak
        else:
            print(f"Failed to get streak for user {username}.")
            return 0
            
    except Exception as e:
        print(f"Error getting user streak: {e}")
        return 0

def update_user_streak(username: str, streak: int):
    try:
        # Update the user's streak
        response = supabase.table("users").update({"streak": streak}).eq("username", username).execute()
        
        if response.status_code == 200:
            print(f"User {username} streak updated successfully.")
            return True
        else:
            print(f"Failed to update streak for user {username}.")
            return False
            
    except Exception as e:
        print(f"Error updating user streak: {e}")
        return False

def update_user_password(user_id, new_password):
    try:
        # Update the user's password
        response = supabase.table("users").update({"password": new_password}).eq("id", user_id).execute()
        
        if response.status_code == 200:
            print(f"User {user_id} password updated successfully.")
            return True
        else:
            print(f"Failed to update password for user {user_id}.")
            return False
            
    except Exception as e:
        print(f"Error updating user password: {e}")
        return False

def add_story(title: str, story_content: str, prompts: dict, word_count: int, points_earned: int, username: str):
    try:
        # Validate input parameters
        if not title or not story_content or not username:
            print("Error: Missing required fields for story")
            return None
            
        story_data = {
            "title": title,
            "story_content": story_content,
            "prompt": prompts,  # This will be stored as JSON in PostgreSQL
            "word_count": word_count,
            "points": points_earned,
            "author_username": username,
            "created_at": datetime.today().isoformat()
        }
        
        # Insert the story into Supabase
        result = supabase.table('stories').insert(story_data).execute()
        
        # Check if the insert was successful
        if result.data and len(result.data) > 0:
            story_id = result.data[0]['id']
            print(f"Story '{title}' saved successfully with ID: {story_id}")
            return story_id
        else:
            print(f"Failed to save story: {result}")
            return None
        
    except Exception as db_error:
        print(f"Database error while saving story: {db_error}")
        return None

def get_user_stories(username: str):
    try:
        # Get stories by author_username (not author_id)
        response = supabase.table("stories").select("*").eq("author_username", username).execute()
        
        if response.data:
            stories = response.data
            print(f"Found {len(stories)} stories for user {username}")
            return stories
        else:
            print(f"No stories found for user {username}.")
            return []
            
    except Exception as e:
        print(f"Error getting user stories: {e}")
        return []

def get_all_stories():
    try:
        # Get all stories
        response = supabase.table("stories").select("*").execute()
        
        if response.status_code == 200 and response.data:
            stories = response.data
            print(f"All stories: {stories}")
            return stories
        else:
            print("Failed to get all stories.")
            return []
            
    except Exception as e:
        print(f"Error getting all stories: {e}")
        return []