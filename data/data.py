import sqlite3
import logging

USER_DATA_FILE = "data/users.db"
STORY_DATA_FILE = "data/stories.db"

def get_db_connection(db_file: str) -> sqlite3.Connection:
    try:
        return sqlite3.connect(db_file)
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database {db_file}: {e}")
        raise

def create_user_db():
    try:
        conn = get_db_connection(USER_DATA_FILE) # connect to the database
        cur = conn.cursor() # create a cursor
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                parent_email TEXT NOT NULL,
                streak INTEGER DEFAULT 0,
                points INTEGER DEFAULT 0
            )
        """)
        conn.commit() # commit the changes
    except sqlite3.Error as e:
        logging.error(f"Error creating user database: {e}")
        raise
    finally:
        conn.close()

def create_stories_db():
    try:
        conn = get_db_connection(STORY_DATA_FILE) # connect to the database
        cur = conn.cursor() # create a cursor
        
        # create the table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stories (
                story_author TEXT NOT NULL,
                story_title TEXT NOT NULL,
                story_contents TEXT NOT NULL,
                story_word_count INTEGER NOT NULL,
                prompts TEXT NOT NULL,
                FOREIGN KEY (story_author) REFERENCES users(username)
            )
        """)
        
        conn.commit() # commit the table/changes
    except sqlite3.Error as e:
        logging.error(f"Error creating stories database: {e}")
        raise
    finally:
        conn.close() # close the connection

def create_databases():
    # create databases
    create_user_db()
    create_stories_db()

# FUNCTIONS FOR ACCESSING DATABASES
def add_user_data(user_data: tuple):
    # connect to the user database
    user_conn = sqlite3.connect(USER_DATA_FILE)
    cur = user_conn.cursor()
    
    cur.execute("INSERT INTO users (username, password, parent_email, streak, points) VALUES (?, ?, ?, ?, ?)", user_data)
    
    # close the database objects
    cur.close()
    user_conn.close()

def add_story_data(story_data: list):
    story_conn = sqlite3.connect(STORY_DATA_FILE)
    cur = story_conn.cursor()
    
    cur.execute("""INSERT INTO stories (story_author, story_title, story_contents, story_word_count, prompts) VALUES (?, ?, ?, ?, ?)""", story_data)
    
    story_conn.commit() # add commit before closing connection
    story_conn.close()

def view_all_user_data():
    # connect to the user database
    user_conn = sqlite3.connect(USER_DATA_FILE)
    cur = user_conn.cursor()

    for row in cur.execute("SELECT * FROM users;"):
        print(row)

    user_conn.close()
    
def find_user(user_name: str):
    user_conn = sqlite3.connect(USER_DATA_FILE)
    cur = user_conn.cursor()
    
    # query to check if the user exists
    cur.execute("SELECT 1 FROM users WHERE username = ?", (user_name,))
    result = cur.fetchone()
    
    user_conn.close()
    
    user_exists = False
    
    if result != None:
        user_exists = True
        
    return user_exists

def login_user(username: str, password: str):
    user_conn = sqlite3.connect(USER_DATA_FILE)
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
        user_conn.close()
        
def get_user_stories(username: str):
    story_conn = sqlite3.connect(STORY_DATA_FILE)
    cur = story_conn.cursor()
    
    cur.execute("SELECT * FROM stories WHERE story_author = ?", (username,))
    user_data = cur.fetchall()
    
    story_conn.close()
    
    return user_data

def get_total_word_count(user_name):
    story_conn = sqlite3.connect(STORY_DATA_FILE)
    cursor = story_conn.cursor()

    # Query to get the total word count for the specified user
    query = """
    SELECT SUM(story_word_count) AS total_words
    FROM stories
    WHERE story_author = ?
    """
    
    try:
        cursor.execute(query, (user_name,))
        total_word_count = cursor.fetchone()[0]
        return total_word_count if total_word_count is not None else 0
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return 0
    
    finally: 
        # close the connection
        story_conn.close()

def get_user_streak(username: str):
    story_conn = sqlite3.connect(STORY_DATA_FILE)
    cursor = story_conn.cursor()

    # SQL query to find the current streak
    query = """
    SELECT COUNT(*) AS streak_length
    FROM (
        SELECT activity_date,
                ROW_NUMBER() OVER (ORDER BY activity_date) - 
                JULIANDAY(activity_date) AS date_gap
        FROM user_activity
        WHERE user_id = ?
    ) AS streaks
    WHERE JULIANDAY('now') - JULIANDAY(activity_date) < COUNT(*);
    """
    
    cursor.execute(query, (username,))
    streak_length = cursor.fetchone()[0]

    # Close the connection
    story_conn.close()

    # Handle the case where the user has no activity
    return streak_length if streak_length is not None else 0

def update_user_streak(username, new_streak):
    user_conn = sqlite3.connect(USER_DATA_FILE)
    cursor = user_conn.cursor()

    # SQL query to update the streak for a specific user
    query = """
    UPDATE users
    SET streak = ?
    WHERE username = ?
    """

    cursor.execute(query, (new_streak, username))
    
    # Commit the changes to the database
    user_conn.commit()

    # Close the connection
    user_conn.close()

    print(f"User {username}'s streak has been updated to {new_streak}.")
    
def change_parent_email(parent_email, username):
    user_conn = sqlite3.connect(USER_DATA_FILE)
    cursor = user_conn.cursor()
    
    # Create new values to update the user
    cursor.execute("UPDATE users SET parent_email = ? WHERE username = ?", (parent_email, username))
    
    # Commit the changes to the database
    user_conn.commit()
    
    # Optionally fetch the newly edited user (not necessary if you're just redirecting)
    cursor.execute("SELECT * FROM users WHERE id = ?", (username))
    edited_user = cursor.fetchone()  # You can process this if needed

    # close the connection
    user_conn.close()
    
def get_user_points(username: str):
    user_conn = sqlite3.connect(USER_DATA_FILE)
    cursor = user_conn.cursor()
    
    try:
        cursor.execute("SELECT points FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        # If result exists, return the points (which is the first column), otherwise return 0
        return result[0] if result else 0
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return 0
        
    finally:
        user_conn.close()

def update_user_points(username: str, new_points: int):
    user_conn = sqlite3.connect(USER_DATA_FILE)
    cursor = user_conn.cursor()

    # SQL query to update the streak for a specific user
    query = """
    UPDATE users
    SET points = ?
    WHERE username = ?
    """

    cursor.execute(query, (new_points, username))
    
    # Commit the changes to the database
    user_conn.commit()

    # Close the connection
    user_conn.close()

    print(f"User {username}'s points have been updated to {new_points}.")
    
def find_story(story_title: str):
    story_conn = sqlite3.connect(STORY_DATA_FILE)
    cursor = story_conn.cursor()
    
    cursor.execute("SELECT * FROM stories WHERE title = ?", (story_title,))
    
    story = cursor.fetchone()
    
    story_conn.close() # close database connection
    return story

def get_parent_email(username: str):
    user_conn = sqlite3.connect(USER_DATA_FILE)
    cursor = user_conn.cursor()
    
    try:
        # query to get the parent email for the specific user
        cursor.execute("SELECT parent_email FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        # return the parent email if found (None if not found)
        return result[0] if result else None
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    
    finally:
        user_conn.close() # close the connection