import sqlite3

USER_DATA = "data/users.db"
STORY_DATA = "data/stories.db"

def add_data(data: list):
    # connect to the database
    conn = sqlite3.connect(USER_DATA)
    
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

def view_data(database_directory: str, table_name: str):
    # connect to the database
    conn = sqlite3.connect(database_directory)
    
    # create a cursor
    cur = conn.cursor()
    
    for row in cur.execute("SELECT * FROM " + table_name+ ";"):
        print(row)
        
    cur.close()
    conn.close()

test_data = [
    ("zkd365", "test"),
    ("sushi", "test")
]

add_data(test_data)