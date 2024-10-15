import sqlite3

USER_DATA = "data/users.db"
STORY_DATA = "data/stories.db"

def get_data(file_path: str):
    # connect to the database
    conn = sqlite3.connect(file_path)
    
    # create a cursor
    cur = conn.cursor()
    
    # create a "users" table
    cur.execute('''CREATE TABLE IF NOT EXISTS users
                (username TEXT, password TEXT)''')
    conn.commit()
    
    # close the database objects
    cur.close()
    conn.close()
    
get_data(STORY_DATA)