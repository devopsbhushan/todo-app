import os
from flask import Flask, render_template, request, redirect, session, flash
from datetime import datetime, date
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ---------------- DB CONNECTION ----------------
def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# ---------------- AUTH ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username=%s", (user,))
        data = cur.fetchone()
        conn.close()

        if data and check_password_hash(data[0], pwd):
            session["user"] = user
            return redirect("/tasks")
        else:
            flash("Invalid credentials")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        pwd = generate_password_hash(request.form["password"])

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username,password) VALUES (%s,%s)", (user, pwd))
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

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks ORDER BY id DESC")
    tasks = cur.fetchall()
    conn.close()

    today = date.today()

    return render_template("index.html", tasks=tasks, today=today, current_user=session["user"])


@app.route("/add", methods=["POST"])
def add():
    if "user" not in session:
        return redirect("/")

    user = request.form["user"]
    task = request.form["task"]
    remark = request.form["remark"]
    target = request.form["target"]
    status = request.form["status"]
    open_date = datetime.now().date()

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO tasks (username, task, remark, open_date, target_date, status)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (user, task, remark, open_date, target, status))

    conn.commit()
    conn.close()

    return redirect("/tasks")


@app.route("/update_status/<int:id>/<status>")
def update_status(id, status):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET status=%s WHERE id=%s", (status, id))
    conn.commit()
    conn.close()
    return redirect("/tasks")


@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s", (id,))
    conn.commit()
    conn.close()
    return redirect("/tasks")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM tasks WHERE status='Pending'")
    pending = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tasks WHERE status='Done'")
    done = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tasks WHERE target_date < CURRENT_DATE AND status!='Done'")
    overdue = cur.fetchone()[0]

    conn.close()

    return render_template("dashboard.html", pending=pending, done=done, overdue=overdue)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
