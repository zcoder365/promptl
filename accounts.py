import data.data

def user_exists(username: str):
    # determine if the user exists
    return data.data.find_user(username)

def add_user(username, password, email):
    is_user = user_exists(username)
    
    if is_user:
        return "User already exists. Can't create a new account with this username."
    
    elif not is_user:
        # add the user with generic info
        # users.insert_one({ 'username': username, 'password': str(hashpass, 'utf-8'), 'parent_email': parent_email, 'points': 0, 'streak': 0, "prizes": 0, "average_words": 0})
        
        # generate the user data
        user_data = [(username, password, parent_email, 0, 0)]
        
        # add the data using the function in the data.py file in the data folder
        data.data.add_user_data(user_data)
    
    elif existing_user: # if the user exists...
        # return the error message
        return 'That username already exists! Try logging in.'
    
def login_check(username: str, password: str):
    logged_in = data.data.login_user(username, password)
    
    return logged_in