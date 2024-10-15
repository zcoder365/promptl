import sqlite3

USER_DATA = "../data/users.db"
WRITING_DATA = "../data/stories.db"

def get_user_data():
    # connect to the database
    conn = sqlite3.connect(USER_DATA)
    
    # close the connection
    conn.close()