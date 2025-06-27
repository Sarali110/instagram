import sqlite3

def get_db_connection():
    conn = sqlite3.connect("app.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS friends (
            user1 TEXT,
            user2 TEXT,
            PRIMARY KEY (user1, user2),
            FOREIGN KEY (user1) REFERENCES users(username),
            FOREIGN KEY (user2) REFERENCES users(username)
        );
    """)

    conn.commit()
    conn.close()
