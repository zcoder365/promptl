import sqlite3

USER_DATA = "../data/users.db"
WRITING_DATA = "../data/stories.db"

# connect to a (new) database
conn = sqlite3.connect(USER_DATA)

# close connection
conn.close()