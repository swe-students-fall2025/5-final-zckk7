from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "hanqi"

MONGO_URI = "mongodb+srv://gz:1234@cluster0.fv25oph.mongodb.net/?appName=Cluster0"

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client.smart_apartment_db
    client.admin.command('ping')
    print("MongoDB connected successfully")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    db = None
    client = None


@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    role = session.get("role")
    if role == "admin":
        return redirect(url_for("admin_dashboard"))
    elif role == "resident":
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "username" not in session or session.get("role") != "resident":
        return redirect(url_for("login"))
    
    if "first_name" not in session and db:
        try:
            user = db.users.find_one({"username": session.get("username")})
            if user:
                session["first_name"] = user.get("first_name", "User")
        except:
            pass
    
    alerts = []
    sensor = None
    if db:
        try:
            alerts = list(db.alerts.find({"status": "new"}))
            sensor = db.sensors.find_one()
        except:
            alerts = []
            sensor = None
    
    return render_template("resident/dashboard.html", alerts=alerts, sensor_data=sensor)


@app.route("/packages")
def packages():
    if "username" not in session or session.get("role") != "resident":
        return redirect(url_for("login"))
    
    pkgs = []
    if db:
        try:
            pkgs = list(db.packages.find())
        except:
            pkgs = []
    return render_template("resident/packages.html", packages=pkgs)


@app.route("/community")
def community():
    if "username" not in session or session.get("role") != "resident":
        return redirect(url_for("login"))
    
    if not db:
        return render_template("resident/community.html", posts=[])
    
    try:
        posts = list(db.community_posts.find().sort("_id", -1))
    except:
        posts = []
    
    return render_template("resident/community.html", posts=posts)


@app.route("/community/create")
def create_post():
    if "username" not in session or session.get("role") != "resident":
        return redirect(url_for("login"))
    return render_template("resident/create_post.html")


@app.route("/community/post/<post_id>")
def post_detail(post_id):
    if "username" not in session or session.get("role") != "resident":
        return redirect(url_for("login"))
    
    post = None
    if db:
        try:
            post = db.community_posts.find_one({"_id": ObjectId(post_id)})
        except:
            post = None
    
    return render_template("resident/post_detail.html", post=post, post_id=post_id)


@app.route("/maintenance/new")
def maintenance():
    if "username" not in session or session.get("role") != "resident":
        return redirect(url_for("login"))
    return render_template("resident/maintenance.html")


@app.route("/admin")
def admin_dashboard():
    if "username" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template("admin/admin.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "")

        if not first_name or not last_name or not username or not password or not role:
            error = "All fields are required."
        elif len(username) < 3:
            error = "Username must be at least 3 characters."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif role not in ["admin", "resident"]:
            error = "Invalid role selected."
        elif db:
            existing_user = db.users.find_one({"username": username})
            if existing_user:
                error = "Username already exists. Please choose another."
            else:
                try:
                    hashed_pw = generate_password_hash(password)
                    db.users.insert_one({
                        "first_name": first_name,
                        "last_name": last_name,
                        "username": username,
                        "password": hashed_pw,
                        "role": role
                    })
                    session["username"] = username
                    session["first_name"] = first_name
                    session["role"] = role
                    if role == "admin":
                        return redirect(url_for("admin_dashboard"))
                    return redirect(url_for("dashboard"))
                except:
                    error = "An error occurred. Please try again."
        else:
            error = "Database connection failed. Please try again later."

    return render_template("signup.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            error = "Username and password are required."
        elif db:
            user = db.users.find_one({"username": username})
            if user and check_password_hash(user["password"], password):
                session["username"] = username
                session["first_name"] = user.get("first_name", "User")
                session["role"] = user["role"]
                if user["role"] == "admin":
                    return redirect(url_for("admin_dashboard"))
                return redirect(url_for("dashboard"))
            else:
                error = "Invalid username or password."
        else:
            error = "Database connection failed. Please try again later."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
