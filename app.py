from flask import Flask, request, render_template, redirect, session, url_for, send_from_directory, jsonify 
from db import get_db_connection, init_db
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super-secret-key"


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# Initialize DB schema once at startup
with app.app_context():
    init_db()


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_post', methods=['POST'])
def upload_post():
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 401

    if 'photo' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['photo']
    caption = request.form.get('caption', '')

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(f"{session['username']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO posts (user, image_path, caption) VALUES (?, ?, ?)", (session['username'], filename, caption))
        conn.commit()
        conn.close()

        return jsonify({"message": "Post uploaded successfully"})

    return jsonify({"error": "Invalid file type"}), 400


@app.route('/timeline')
def timeline():
    if 'username' not in session:
        return jsonify({"error": "Not logged in"}), 401

    user = session['username']
    conn = get_db_connection()
    cur = conn.cursor()

    # Get posts from user and friends, ordered newest first
    cur.execute("""
        SELECT p.user, p.image_path, p.caption, p.timestamp
        FROM posts p
        WHERE p.user = ?
        OR p.user IN (
            SELECT user2 FROM friendships WHERE user1 = ?
            UNION
            SELECT user1 FROM friendships WHERE user2 = ?
        )
        ORDER BY p.timestamp DESC
    """, (user, user, user))

    posts = cur.fetchall()
    conn.close()

    result = [
        {
            "user": row["user"],
            "image_url": f"/uploads/{row['image_path']}",
            "caption": row["caption"],
            "timestamp": row["timestamp"]
        }
        for row in posts
    ]

    return jsonify(result)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("profile"))
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    username = request.form.get("username")
    password = request.form.get("password")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    if cur.fetchone():
        conn.close()
        return render_template("signup.html", error="Username already exists")

    cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username")
    password = request.form.get("password")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()

    if not row or row["password"] != password:
        return render_template("login.html", error="Invalid credentials")

    session["username"] = username
    return redirect(url_for("profile"))

@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for("login"))
    username = session["username"]

    # Get friends list
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT user2 FROM friendships WHERE user1 = ?
        UNION
        SELECT user1 FROM friendships WHERE user2 = ?
    """, (username, username))
    friends = [row[0] for row in cur.fetchall()]
    conn.close()

    return render_template("profile.html", username=username, friends=friends)

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/add_friend", methods=["POST"])
def add_friend():
    if "username" not in session:
        return redirect(url_for("login"))

    user = session["username"]
    friend = request.form.get("friend")

    if user == friend:
        return render_template("profile.html", username=user, friends=get_friends_list(user), error="You cannot add yourself as a friend")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM users WHERE username = ?", (friend,))
    if not cur.fetchone():
        conn.close()
        return render_template("profile.html", username=user, friends=get_friends_list(user), error=f"User '{friend}' does not exist")

    cur.execute("INSERT OR IGNORE INTO friendships (user1, user2) VALUES (?, ?)", (user, friend))
    cur.execute("INSERT OR IGNORE INTO friendships (user1, user2) VALUES (?, ?)", (friend, user))
    conn.commit()
    conn.close()

    return redirect(url_for("profile"))

@app.route("/remove_friend", methods=["POST"])
def remove_friend():
    if "username" not in session:
        return redirect(url_for("login"))

    user = session["username"]
    friend = request.form.get("friend")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM friendships WHERE user1 = ? AND user2 = ?", (user, friend))
    cur.execute("DELETE FROM friendships WHERE user1 = ? AND user2 = ?", (friend, user))
    conn.commit()
    conn.close()

    return redirect(url_for("profile"))

def get_friends_list(username):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT user2 FROM friendships WHERE user1 = ?
        UNION
        SELECT user1 FROM friendships WHERE user2 = ?
    """, (username, username))
    friends = [row[0] for row in cur.fetchall()]
    conn.close()
    return friends

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
