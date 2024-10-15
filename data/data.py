import sqlite3

USER_DATA = "../data/users.db"
WRITING_DATA = "../data/stories.db"

def get_user_data():
    # connect to the database
    conn = sqlite3.connect(USER_DATA)
    
    # create a cursor
    cur = conn.cursor()
    
    # create a "users" table
    cur.execute('''CREATE TABLE IF NOT EXISTS users
                (username TEXT, password TEXT)''')
    conn.commit()
    
    # close the database objects
    cur.close()
    conn.close()