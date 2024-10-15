import sqlite3

USER_DATA_FILE = "data/users.db"
USER_DATA_TABLE = "users"

STORY_DATA_FILE = "data/stories.db"
STORY_DATA_TABLE = "stories"

def add_user_data(user_data: list):
    # connect to the database
    conn = sqlite3.connect(USER_DATA_FILE)
    
    # create a cursor
    cur = conn.cursor()
    
    # create a "users" table
    cur.execute('''CREATE TABLE IF NOT EXISTS users
                (username TEXT, password TEXT, parent_email TEXT, points INTEGER, streak INTEGER)''')
    conn.commit()
    
    cur.executemany("""INSERT INTO users (username, password) VALUES (?, ?)""", user_data)
    
    # close the database objects
    cur.close()
    conn.close()

def add_story_data(story_data: list):
    conn = sqlite3.connect(STORY_DATA_FILE)
    cur = conn.cursor()
    
    cur.execute('''CREATE TABLE IF NOT EXISTS users
                (story_title TEXT, story_contents TEXT, story_word_count INTEGER)''')
    conn.commit()
    
    cur.executemany("""INSERT INTO""" + STORY_DATA_TABLE + """(story_title, story_contents, story_word_count) VALUES (?, ?)""", story_data)
    
    cur.close()
    conn.close()

def view_user_data():
    # connect to the database
    conn = sqlite3.connect(USER_DATA_FILE)

    # create a cursor
    cur = conn.cursor()

    for row in cur.execute("SELECT * FROM users;"):
        print(row)
        
    cur.close()
    conn.close()
    
def find_user(user_name: str):
    conn = sqlite3.connect(USER_DATA_FILE)
    cur = conn.cursor()
    
    # query to check if the user exists
    cur.execute("SELECT 1 FROM " + USER_DATA_TABLE + " WHERE user_name = ?", (user_name))
    result = cur.fetchone()
    
    conn.close()
    
    return result is not None