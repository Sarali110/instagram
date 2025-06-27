from flask import Flask, request, jsonify, render_template
from db import get_db_connection, init_db

app = Flask(__name__)
init_db()

# In-memory storage
# users = {}  # username -> password
# friends = {}  # username -> set of friends

@app.route("/")
def home():
    return render_template("index.html")

@app.post("/signup")
def signup():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")


  #  if username in users:
  #      return jsonify({"error": "Username already exists"}), 400
  #
  #  users[username] = password
  #  friends[username] = set()
  
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    if cur.fetchone():
        return jsonify({"error": "Username already exists"}), 400

    cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()
    return jsonify({"message": "User created successfully"}), 201

@app.post("/login")
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    #if users.get(username) != password:
    #    return jsonify({"error": "Invalid credentials"}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    
    if not row or row["password"] != password:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"message": "Login successful"})

@app.post("/add_friend")
def add_friend():
    data = request.get_json()
    user = data.get("user")
    friend = data.get("friend")

    #if user not in users or friend not in users:
    #    return jsonify({"error": "User or friend does not exist"}), 400

    if user == friend:
        return jsonify({"error": "Cannot add yourself as a friend"}), 400

    #friends[user].add(friend)
    #friends[friend].add(user)
    conn = get_db_connection()
    cur = conn.cursor()

    # Check if both users exist
    cur.execute("SELECT 1 FROM users WHERE username = ?", (user,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"error": f"User '{user}' does not exist"}), 400

    cur.execute("SELECT 1 FROM users WHERE username = ?", (friend,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"error": f"Friend '{friend}' does not exist"}), 400

    # Add friendship in both directions
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

    #if user not in users or friend not in users:
    #    return jsonify({"error": "User or friend does not exist"}), 400

    #friends[user].discard(friend)
    #friends[friend].discard(user)
    conn = get_db_connection()
    cur = conn.cursor()

    # Check if both users exist
    cur.execute("SELECT 1 FROM users WHERE username = ?", (user,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"error": f"User '{user}' does not exist"}), 400

    cur.execute("SELECT 1 FROM users WHERE username = ?", (friend,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"error": f"Friend '{friend}' does not exist"}), 400

    # Remove friendship from both directions
    cur.execute("DELETE FROM friends WHERE user1 = ? AND user2 = ?", (user, friend))
    cur.execute("DELETE FROM friends WHERE user1 = ? AND user2 = ?", (friend, user))

    conn.commit()
    conn.close()

    return jsonify({"message": f"{user} and {friend} are no longer friends"})

@app.get("/friends/<username>")
def get_friends(username):
    #if username not in users:
    #    return jsonify({"error": "User does not exist"}), 404

    #return jsonify({"friends": list(friends[username])})
    conn = get_db_connection()
    cur = conn.cursor()

    # Check if the user exists
    cur.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    if not cur.fetchone():
        conn.close()
        return jsonify({"error": "User does not exist"}), 404

    # Fetch all friends where user is either user1 or user2
    cur.execute("""
        SELECT user2 FROM friends WHERE user1 = ?
        UNION
        SELECT user1 FROM friends WHERE user2 = ?
    """, (username, username))

    result = cur.fetchall()
    conn.close()

    # Extract friend usernames into a list
    friend_list = [row[0] for row in result]

    return jsonify({"friends": friend_list})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
