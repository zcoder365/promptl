from helpers.database import db

def add_user(username: str, password: str, email: str):
    is_user = db.find_user(username)
    
    if is_user:
        return "User already exists. Can't create a new account with this username."
    
    elif not is_user:
        # generate the user data
        user_data = (username, password, email, 0, 0)
        
        # add the data using the function in the data.py file in the data folder
        db.add_user_data(user_data)
    
def login_check(username: str, password: str):
    logged_in = db.login_user(username, password)
    
    return logged_in