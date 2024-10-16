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
    
    cur.execute("""INSERT INTO""" + STORY_DATA_TABLE + """(story_author, story_title, story_contents, story_word_count, prompts) VALUES (?, ?, ?, ?)""", story_data)
    
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
        user_conn.close()
        
def get_user_stories(user_name: str):
    cur = story_conn.cursor()
    
    cur.execute("SELECT * FROM users WHERE author = ?", (user_name))
    user_data = cur.fetchall()
    
    story_conn.close()
    
    return user_data

def get_total_word_count(user_name):
    cursor = story_conn.cursor()

    # Query to get the total word count for the specified user
    query = """
    SELECT SUM(LENGTH(content) - LENGTH(REPLACE(content, ' ', '')) + 1) AS total_words
    FROM stories
    WHERE user_id = ?
    """
    
    cursor.execute(query, (user_name,))
    total_word_count = cursor.fetchone()[0]

    # Close the connection
    story_conn.close()

    # Handle the case where the user has no posts
    return total_word_count if total_word_count is not None else 0

def get_user_streak(user_identifier):
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
    
    cursor.execute(query, (user_identifier,))
    streak_length = cursor.fetchone()[0]

    # Close the connection
    story_conn.close()

    # Handle the case where the user has no activity
    return streak_length if streak_length is not None else 0

def update_user_streak(username, new_streak):
    cursor = user_conn.cursor()

    # SQL query to update the streak for a specific user
    query = """
    UPDATE users
    SET streak = ?
    WHERE username = ?
    """

    cursor.execute(query, (new_streak, username))
    
    # Commit the changes to the database
    story_conn.commit()

    # Close the connection
    story_conn.close()

    print(f"User {username}'s streak has been updated to {new_streak}.")
    
def change_parent_email(parent_email, username):
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
    cursor = user_conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username))
    user = cursor.fetchone()
    points = user[4]
    
    return points

def update_user_points(username: str, new_points: int):
    cursor = user_conn.cursor()

    # SQL query to update the streak for a specific user
    query = """
    UPDATE users
    SET points = ?
    WHERE username = ?
    """

    cursor.execute(query, (new_points, username))
    
    # Commit the changes to the database
    story_conn.commit()

    # Close the connection
    story_conn.close()

    print(f"User {username}'s points have been updated to {new_points}.")
    
def find_story(story_title: str):
    pass