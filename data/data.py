import sqlite3

USER_DATA_FILE = "data/users.db"
USER_DATA_TABLE = "users"

STORY_DATA_FILE = "data/stories.db"
STORY_DATA_TABLE = "stories"

user_conn = sqlite3.connect(USER_DATA_FILE)
story_conn = sqlite3.connect(STORY_DATA_FILE)

def add_user_data(user_data: list):
    # create a cursor
    cur = user_conn.cursor()
    
    cur.execute("INSERT INTO" + USER_DATA_TABLE + "(username, password, parent_email, streak, points) VALUES (?, ?, ?, ?, ?)", user_data)
    
    # close the database objects
    cur.close()
    user_conn.close()

def add_story_data(story_data: list):
    cur = story_conn.cursor()
    
    cur.execute("""INSERT INTO""" + STORY_DATA_TABLE + """(story_author, story_title, story_contents, story_word_count) VALUES (?, ?, ?, ?)""", story_data)
    
    story_conn.close()

def view_all_user_data():
    # create a cursor
    cur = user_conn.cursor()

    for row in cur.execute("SELECT * FROM users;"):
        print(row)

    user_conn.close()
    
def find_user(user_name: str):
    cur = user_conn.cursor()
    
    # query to check if the user exists
    cur.execute("SELECT 1 FROM " + USER_DATA_TABLE + " WHERE user_name = ?", (user_name))
    result = cur.fetchone()
    
    user_conn.close()
    
    return result is not None

def login_user(username: str, password: str):
    cur = user_conn.cursor()
    
    try:
        cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        result = cur.fetchone()
        
        if result:
            print("Login successful!")
            return True
    
        else:
            print("Login failed. Invalid username or password.")
            return False
        
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return False
    
    finally:
        conn.close()
        
def get_user_stories(user_name: str):
    cur = story_conn.cursor()