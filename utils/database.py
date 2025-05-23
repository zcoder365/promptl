from supabase import create_client
import os
from dotenv import load_dotenv
import bcrypt
from datetime import datetime

# load the environment variables from the .env file
load_dotenv() # load the file
SUPABASE_URL = os.getenv("SUPABASE_URI") # get the database uri
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") # get the database key

# initialize the supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_user(username: str, password: str):
    try:
        # hash the password before storing
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # create a user entry
        new_user_entry = {
            "username": username,
            "password": hashed_password.decode('utf-8') # Store as string
        }
        
        # add a user to the database
        response = supabase.table("users").insert(new_user_entry).execute()
        
        return response.data
        
    except Exception as e:
        print(f"Error adding user: {e}")
        return None
    
def get_user(username: str):
    try:
        # Execute the query - errors will be raised as exceptions
        response = supabase.table("users").select("*").eq("username", username).execute()
        
        # Debug: Print what we got back
        print(f"Debug - get_user response data: {response.data}")
        print(f"Debug - Data length: {len(response.data) if response.data else 0}")
        
        # Check if we got any data back
        if response.data and len(response.data) > 0:
            user = response.data[0]
            print(f"Debug - Found user: {user}")
            return user  # Return single user object
        else:
            # No user found with that username
            print(f"Debug - No user found with username: {username}")
            return None
            
    except Exception as e:
        # Handle any database errors that occur
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

def add_story(title: str, story_content: str, prompts: dict, word_count: int, points_earned: int, username: str):
    created_at = datetime.now().isoformat()  # Get the current date and time in ISO format
    try:
        # Create a new story entry
        new_story_entry = {
            "title": title,
            "story_content": story_content,
            "prompt": prompts,
            "word_count": word_count,
            "points_earned": points_earned,
            "author_id": username,  # Assuming username is unique
            "created_at": created_at
        }
        
        # Add the story to the database
        response = supabase.table("stories").insert(new_story_entry).execute()
        
        if response.status_code == 201:
            print(f"Story '{title}' added successfully.")
            return True
        else:
            print(f"Failed to add story '{title}'.")
            return False
            
    except Exception as e:
        print(f"Error adding story: {e}")
        return False

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