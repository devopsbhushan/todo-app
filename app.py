from flask import Flask, render_template, request, redirect, session, flash
import requests, json, base64, os
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecret"

# ---------------- GITHUB CONFIG ----------------
TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPO")   # username/repo
FILE_PATH = "db.json"

# ---------------- LOAD DATA ----------------
def load_data():
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {TOKEN}"}

    res = requests.get(url, headers=headers)

    if res.status_code != 200:
        print("GitHub API Error:", res.json())
        raise Exception("Failed to load db.json from GitHub")

    res_json = res.json()

    # SAFETY CHECK
    if "content" not in res_json:
        print("Invalid response:", res_json)
        raise Exception("No content found in GitHub response")

    content = base64.b64decode(res_json["content"]).decode()
    return json.loads(content), res_json["sha"]

# ---------------- SAVE DATA ----------------
def save_data(data, sha):
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {TOKEN}"}

    encoded = base64.b64encode(json.dumps(data, indent=4).encode()).decode()

    payload = {
        "message": "update db",
        "content": encoded,
        "sha": sha
    }

    res = requests.put(url, json=payload, headers=headers)

    if res.status_code not in [200, 201]:
        print("Save Error:", res.json())
        raise Exception("Failed to save data")

# ---------------- AUTH ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        data, _ = load_data()

        for u in data["users"]:
            print("DB USER:", u["username"])
            print("INPUT USER:", user)

            if u["username"] == user:
                print("USERNAME MATCH")

            if u["username"] == user and check_password_hash(u["password"], pwd):
                print("LOGIN SUCCESS")
               session["user"] = user
                return redirect("/tasks")

        flash("Invalid credentials")

    return render_template("login.html")


@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        data, sha = load_data()

        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        # check duplicate
        for u in data["users"]:
            if u["username"] == username:
                flash("User already exists")
                return redirect("/register")

        data["users"].append({
            "username": username,
            "password": password
        })

        save_data(data, sha)
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

    data, _ = load_data()
    today = date.today().strftime("%Y-%m-%d")

    return render_template("index.html", tasks=data["tasks"], today=today, current_user=session["user"])


@app.route("/add", methods=["POST"])
def add():
    data, sha = load_data()

    new_task = {
        "id": len(data["tasks"]) + 1,
        "user": request.form["user"],
        "task": request.form["task"],
        "remark": request.form["remark"],
        "target": request.form["target"],
        "status": request.form["status"],
        "open_date": datetime.now().strftime("%Y-%m-%d")
    }

    data["tasks"].append(new_task)
    save_data(data, sha)

    return redirect("/tasks")


@app.route("/update/<int:id>/<status>")
def update(id, status):
    data, sha = load_data()

    for t in data["tasks"]:
        if t["id"] == id:
            t["status"] = status

    save_data(data, sha)
    return redirect("/tasks")


@app.route("/delete/<int:id>")
def delete(id):
    data, sha = load_data()

    data["tasks"] = [t for t in data["tasks"] if t["id"] != id]

    save_data(data, sha)
    return redirect("/tasks")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    data, _ = load_data()
    today = date.today().strftime("%Y-%m-%d")

    pending = sum(1 for t in data["tasks"] if t["status"] == "Pending")
    done = sum(1 for t in data["tasks"] if t["status"] == "Done")
    overdue = sum(1 for t in data["tasks"] if t["target"] < today and t["status"] != "Done")

    return render_template("dashboard.html", pending=pending, done=done, overdue=overdue)

if __name__ == "__main__":
    app.run(debug=True)
