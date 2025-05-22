from supabase import create_client, Client
import os
from dotenv import load_dotenv
import bcrypt
from datetime import datetime

# load the environment variables from the .env file
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

def add_user(username: str, password: str):
    try:
        # Hash the password before storing
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # create a user entry
        new_user_entry = {
            "username": username,
            "password": hashed_password.decode('utf-8')  # Store as string
        }
        
        # add a user to the database
        response = supabase.table("users").insert(new_user_entry).execute()
        
        print(f"Debug - add_user response: {response.data}")
        return response.data
        
    except Exception as e:
        print(f"Error adding user: {e}")
        return None