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
        # validate inputs before database operation
        if not username or not password:
            print("Error: Username or password is empty")
            return None
        
        print(f"Debug - Attempting to add user: {username}")
        print(f"Debug - Password hash length: {len(password)}")
        
        # create user entry with hashed password
        new_user_entry = {
            "username": username,
            "password": password  # This should already be hashed
        }
        
        # insert into database
        print(f"Debug - Inserting user entry: {new_user_entry}")
        response = supabase.table("users").insert(new_user_entry).execute()
        
        # debug: Print the full response to see what Supabase returns
        print(f"Debug - Supabase response: {response}")
        print(f"Debug - Response data: {response.data}")
        print(f"Debug - Response data type: {type(response.data)}")
        
        # Check if the insertion was successful
        if response.data and len(response.data) > 0:
            print(f"Successfully created user: {username}")
            
            return response.data[0]  # Return the created user data
        
        else:
            print(f"Failed to create user: {username}")
            print(f"Debug - Response.data is: {response.data}")
            
            # check if there are any errors in the response
            if hasattr(response, 'error') and response.error:
                print(f"Debug - Supabase error: {response.error}")
            
            return None
            
    except Exception as e:
        # log the specific error for debugging
        print(f"Database error adding user '{username}': {e}")
        print(f"Debug - Exception type: {type(e)}")
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
        
        if response.data:
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
        
        if response.data:
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
        
        print(f"DEBUG DB - Adding story for user: {username}")
        print(f"DEBUG DB - Story title: {title}")
        print(f"DEBUG DB - Word count: {word_count}")
        print(f"DEBUG DB - Points: {points_earned}")
        
        # Check if supabase client is properly initialized
        if not supabase:
            print("Error: Supabase client not initialized")
            return None
            
        story_data = {
            "title": title,
            "story": story_content,
            "prompts": prompts,  # This will be stored as JSON in PostgreSQL
            "word_count": word_count,
            "points_earned": points_earned,
            "author_username": username,  # Using username instead of author_id
            "created_at": datetime.now().isoformat()
        }
        
        # Debug: Print the data being sent
        print(f"DEBUG DB - Story data: {story_data}")
        
        # Insert the story into Supabase with better error handling
        result = supabase.table('stories').insert(story_data).execute()
        
        # Debug: Print the full result object
        print(f"DEBUG DB - Insert result: {result}")
        print(f"DEBUG DB - Result data: {result.data}")
        print(f"DEBUG DB - Result count: {result.count if hasattr(result, 'count') else 'No count'}")
        
        # Check for errors in the result
        if hasattr(result, 'error') and result.error:
            print(f"Supabase error: {result.error}")
            return None
        
        # Check if the insert was successful
        if result.data and len(result.data) > 0:
            story_id = result.data[0]['id']
            print(f"Story '{title}' saved successfully with ID: {story_id}")
            
            # Update user's total points and word count
            update_user_points(username, points_earned)
            update_user_word_count(username, word_count)
            
            return story_id
        
        else:
            print(f"No data returned from insert operation")
            print(f"Full result object: {vars(result)}")  # Print all attributes of result
            return None
        
    except Exception as db_error:
        print(f"Database error while saving story: {db_error}")
        print(f"Error type: {type(db_error)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return None

def get_user_stories(username: str):
    """Get all stories written by a specific user"""
    try:
        # Get stories by author_username (not author_id)
        response = supabase.table("stories").select("*").eq("author_username", username).order("created_at", desc=True).execute()
        
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
    """Get all stories from the database"""
    try:
        # Get all stories ordered by creation date
        response = supabase.table("stories").select("*").order("created_at", desc=True).execute()
        
        if response.data:
            stories = response.data
            print(f"Retrieved {len(stories)} total stories")
            return stories
        else:
            print("No stories found in database.")
            return []
            
    except Exception as e:
        print(f"Error getting all stories: {e}")
        return []