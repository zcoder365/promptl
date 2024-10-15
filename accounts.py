import os
import data.data

def user_exists(username: str, password: str, parent_email: str):
    # determine if the user exists
    existing_user = data.data.find_user(username)
    
    if not existing_user: # if user doesn't exist...
        # add the user with generic info
        # users.insert_one({ 'username': username, 'password': str(hashpass, 'utf-8'), 'parent_email': parent_email, 'points': 0, 'streak': 0, "prizes": 0, "average_words": 0})
        
        # generate the user data
        user_data = [(username, password, parent_email, 0, 0)]
        
        # add the data using the function in the data.py file in the data folder
        data.data.add_user_data(user_data)
    
    elif existing_user: # if the user exists...
        # return the error message
        return 'That username already exists! Try logging in.'