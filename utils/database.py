from supabase import create_client
import os
from dotenv import load_dotenv
import bcrypt
from datetime import datetime

# load the environment variables from the .env file
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

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