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
    try:
        # Update the user's points
        response = supabase.table("users").update({"points": points_to_add}).eq("username", username).execute()
        
        if response.status_code == 200:
            print(f"User {username} points updated successfully.")
            return True
        else:
            print(f"Failed to update points for user {username}.")
            return False
            
    except Exception as e:
        print(f"Error updating user points: {e}")
        return False

def update_user_word_count(username: str, word_count_to_add: int):
    try:
        # Update the user's word count
        response = supabase.table("users").update({"total_word_count": word_count_to_add}).eq("username", username).execute()
        
        if response.status_code == 200:
            print(f"User {username} word count updated successfully.")
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
        
        if response.status_code == 200 and response.data:
            streak = response.data[0]['streak']
            print(f"User {username} streak: {streak}")
            return streak
        else:
            print(f"Failed to get streak for user {username}.")
            return None
            
    except Exception as e:
        print(f"Error getting user streak: {e}")
        return None

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
        # Convert ObjectId to string for Supabase (PostgreSQL doesn't support ObjectId)
        story_data = {
            "title": title,
            "story_content": story_content,
            "prompt": prompts,  # This will be stored as JSON
            "word_count": word_count,
            "points": points_earned,
            "author_username": username,  # Convert ObjectId to string
            "created_at": datetime.today().isoformat()  # Convert datetime to ISO string
        }
        
        # Insert the story into Supabase
        result = supabase.table('stories').insert(story_data).execute()
        
        print(f"Story saved successfully with ID: {result.data[0]['id']}")
        
        return result.data[0]['id']  # Return the ID of the inserted story
        
    except Exception as db_error:
        print(f"Database error: {db_error}")
        return None

def get_user_stories(username: str):
    try:
        # Get the user's stories
        response = supabase.table("stories").select("*").eq("author_id", username).execute()
        
        if response.status_code == 200 and response.data:
            stories = response.data
            print(f"User {username} stories: {stories}")
            return stories
        else:
            print(f"Failed to get stories for user {username}.")
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