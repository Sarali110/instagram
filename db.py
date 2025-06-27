import os
import sqlite3

def get_db_connection():
    db_path = os.path.abspath("app.db")
    print(f"Connecting to DB at: {db_path}")
    conn = sqlite3.connect(db_path)
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
        CREATE TABLE IF NOT EXISTS friendships (
            user1 TEXT,
            user2 TEXT,
            PRIMARY KEY (user1, user2),
            FOREIGN KEY (user1) REFERENCES users(username),
            FOREIGN KEY (user2) REFERENCES users(username)
        );
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            image_path TEXT NOT NULL,
            caption TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user) REFERENCES users(username)
        );
    """)

    conn.commit()
    conn.close()
