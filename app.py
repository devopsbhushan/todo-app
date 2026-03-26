from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DB ----------------
def init_db():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        task TEXT,
        remark TEXT,
        status TEXT,
        open_date TEXT,
        target_date TEXT,
        status TEXT DEFAULT 'Pending'
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- AUTH ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        conn = sqlite3.connect("tasks.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
        data = cursor.fetchone()
        conn.close()

        if data:
            session["user"] = user
            return redirect("/tasks")
        else:
            flash("Invalid Credentials")

    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        conn = sqlite3.connect("tasks.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username,password) VALUES (?,?)",(user,pwd))
            conn.commit()
        except:
            flash("User already exists")
        conn.close()
        return redirect("/")

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- TASKS ----------------
@app.route("/tasks")
def tasks():
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    data = cursor.fetchall()
    conn.close()

    today = datetime.now().date()

    return render_template("index.html", tasks=data, today=today)

@app.route("/add", methods=["POST"])
def add():
    user = request.form["user"]
    task = request.form["task"]
    remark = request.form["remark"]
    target = request.form["target"]

    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (user,task,remark,target_date) VALUES (?,?,?,?)",
                   (user,task,remark,target))
    conn.commit()
    conn.close()

    return redirect("/tasks")

@app.route("/complete/<int:id>")
def complete(id):
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status='Done' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/tasks")

@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/tasks")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status='Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE status='Done'")
    done = cursor.fetchone()[0]

    conn.close()

    return render_template("dashboard.html", pending=pending, done=done)

if __name__ == "__main__":
    app.run(debug=True)
