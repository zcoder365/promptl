import sqlite3

USER_DATA_FILE = "data/users.db"
USER_DATA_TABLE = "users"

STORY_DATA_FILE = "data/stories.db"
STORY_DATA_TABLE = "stories"

def add_data(data: list):
    # connect to the database
    conn = sqlite3.connect(USER_DATA_FILE)
    
    # create a cursor
    cur = conn.cursor()
    
    # create a "users" table
    cur.execute('''CREATE TABLE IF NOT EXISTS users
                (username TEXT, password TEXT)''')
    conn.commit()
    
    cur.executemany("""INSERT INTO users (username, password) VALUES (?, ?)""", test_data)
    
    # close the database objects
    cur.close()
    conn.close()

test_data = [
    ("zkd365", "test"),
    ("sushi", "test")
]

# add_data(test_data)

# connect to the database
conn = sqlite3.connect(USER_DATA_FILE)

# create a cursor
cur = conn.cursor()

for row in cur.execute("SELECT * FROM users;"):
    print(row)
    
cur.close()
conn.close()