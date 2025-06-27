from flask import Flask, request, jsonify, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection, init_db

app = Flask(__name__)
init_db()

# ---------- Helper Functions ----------

def error_response(message, status=400):
    return jsonify({"error": message}), status

def user_exists(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def get_user_password(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row["password"] if row else None

# ---------- Routes ----------

@app.route("/")
def home():
    return render_template("index.html")

@app.post("/signup")
def signup():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if user_exists(username):
        return error_response("Username already exists")

    hashed = generate_password_hash(password)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
    conn.commit()
    conn.close()

    return jsonify({"message": "User created successfully"}), 201

@app.post("/login")
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    hashed = get_user_password(username)

    if not hashed or not check_password_hash(hashed, password):
        return error_response("Invalid credentials", 401)

    return jsonify({"message": "Login successful"})

@app.post("/add_friend")
def add_friend():
    data = request.get_json()
    user = data.get("user")
    friend = data.get("friend")

    if user == friend:
        return error_response("Cannot add yourself as a friend")

    if not user_exists(user):
        return error_response(f"User '{user}' does not exist")
    if not user_exists(friend):
        return error_response(f"Friend '{friend}' does not exist")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO friends (user1, user2) VALUES (?, ?)", (user, friend))
    cur.execute("INSERT OR IGNORE INTO friends (user1, user2) VALUES (?, ?)", (friend, user))
    conn.commit()
    conn.close()

    return jsonify({"message": f"{user} and {friend} are now friends"})

@app.post("/remove_friend")
def remove_friend():
    data = request.get_json()
    user = data.get("user")
    friend = data.get("friend")

    if not user_exists(user):
        return error_response(f"User '{user}' does not exist")
    if not user_exists(friend):
        return error_response(f"Friend '{friend}' does not exist")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM friends WHERE user1 = ? AND user2 = ?", (user, friend))
    cur.execute("DELETE FROM friends WHERE user1 = ? AND user2 = ?", (friend, user))
    conn.commit()
    conn.close()

    return jsonify({"message": f"{user} and {friend} are no longer friends"})

@app.get("/friends/<username>")
def get_friends(username):
    if not user_exists(username):
        return error_response("User does not exist", 404)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT user2 FROM friends WHERE user1 = ?
        UNION
        SELECT user1 FROM friends WHERE user2 = ?
    """, (username, username))

    rows = cur.fetchall()
    conn.close()

    friend_list = [row[0] for row in rows]
    return jsonify({"friends": friend_list})

# ---------- Run Server ----------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
