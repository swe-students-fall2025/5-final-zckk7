import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import certifi

app = Flask(__name__)
app.secret_key = "hanqi"

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MONGO_URI = "mongodb+srv://app_user:7oVLGtXe9dUQWnlB@cluster0.fv25oph.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

db = None
try:
    client = MongoClient(
        MONGO_URI,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=5000,
    )
    client.admin.command("ping")
    db = client.smart_apartment_db
    print("MongoDB connected successfully")
except Exception as e:
    print("MongoDB connection failed:")
    print(e)
    client = None


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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
    
    if "first_name" not in session and db is not None:
        try:
            user = db.users.find_one({"username": session.get("username")})
            if user:
                session["first_name"] = user.get("first_name", "User")
        except:
            pass
    
    alerts = []
    sensor = None
    if db is not None:
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
    if db is not None:
        try:
            pkgs = list(db.packages.find())
        except:
            pkgs = []
    return render_template("resident/packages.html", packages=pkgs)


@app.route("/community")
def community():
    if session.get("role") != "resident":
        return redirect(url_for("login"))
    
    category = request.args.get("category", "all")
    search_query = request.args.get("search", "").strip()
    
    query = {}
    if category != "all":
        if category == "food":
            query["category"] = "Food"
        elif category == "furniture":
            query["category"] = "Furniture"
        elif category == "help":
            query["category"] = "Other"
    
    if search_query:
        query["$or"] = [
            {"title": {"$regex": search_query, "$options": "i"}},
            {"description": {"$regex": search_query, "$options": "i"}}
        ]
    
    posts = list(db.community_posts.find(query).sort("created_at", -1))
    now = datetime.now()
    username = session.get("username", "")
    for post in posts:
        post["_id"] = str(post["_id"])
        post["is_author"] = post.get("author") == username
        if "created_at" in post and post["created_at"]:
            time_diff = (now - post["created_at"]).total_seconds()
            if time_diff < 3600:
                post["time_ago"] = f"{int(time_diff / 60)}m ago"
            elif time_diff < 86400:
                post["time_ago"] = f"{int(time_diff / 3600)}h ago"
            else:
                post["time_ago"] = f"{int(time_diff / 86400)}d ago"
        else:
            post["time_ago"] = "Just now"
    
    return render_template("resident/community.html", posts=posts, current_category=category, search_query=search_query)


@app.route("/community/create", methods=["GET", "POST"])
def create_post():
    if session.get("role") != "resident":
        return redirect(url_for("login"))
    
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "")
        description = request.form.get("description", "").strip()
        
        if not title or not category or not description:
            return render_template("resident/create_post.html", error="All fields are required.")
        
        image_url = ""
        if "image" in request.files:
            file = request.files["image"]
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                filename = timestamp + filename
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(filepath)
                image_url = f"/static/uploads/{filename}"
        
        if category == "Food":
            category_label = "Food"
        elif category == "Furniture":
            category_label = "Furniture"
        else:
            category_label = "Other"
        
        username = session.get("username", "Anonymous")
        author_apt = session.get("apartment_number", "")
        
        post_data = {
            "title": title,
            "category": category_label,
            "description": description,
            "image_url": image_url,
            "author": username,
            "author_apt": author_apt,
            "created_at": datetime.now(),
            "status": "available"
        }
        
        db.community_posts.insert_one(post_data)
        return redirect(url_for("community"))
    
    return render_template("resident/create_post.html")


@app.route("/community/post/<post_id>")
def post_detail(post_id):
    if session.get("role") != "resident":
        return redirect(url_for("login"))
    
    try:
        post = db.community_posts.find_one({"_id": ObjectId(post_id)})
        if not post:
            return redirect(url_for("community"))
        post["_id"] = str(post["_id"])
        
        now = datetime.now()
        if "created_at" in post and post["created_at"]:
            time_diff = (now - post["created_at"]).total_seconds()
            if time_diff < 3600:
                post["time_ago"] = f"{int(time_diff / 60)} mins ago"
            elif time_diff < 86400:
                post["time_ago"] = f"{int(time_diff / 3600)} hours ago"
            else:
                post["time_ago"] = f"{int(time_diff / 86400)} days ago"
        else:
            post["time_ago"] = "Just now"
        
        comments = list(db.comments.find({"post_id": post_id}).sort("created_at", 1))
        for comment in comments:
            comment["_id"] = str(comment["_id"])
            if "created_at" in comment and comment["created_at"]:
                time_diff = (now - comment["created_at"]).total_seconds()
                if time_diff < 3600:
                    comment["time_ago"] = f"{int(time_diff / 60)} mins ago"
                elif time_diff < 86400:
                    comment["time_ago"] = f"{int(time_diff / 3600)} hours ago"
                else:
                    comment["time_ago"] = f"{int(time_diff / 86400)} days ago"
            else:
                comment["time_ago"] = "Just now"
        
        username = session.get("username", "")
        post_author = post.get("author", "")
        is_author = post_author.lower() == username.lower() or username.lower() in post_author.lower()
        
        return render_template("resident/post_detail.html", post=post, comments=comments, is_author=is_author)
    except:
        return redirect(url_for("community"))


@app.route("/community/post/<post_id>/comment", methods=["POST"])
def add_comment(post_id):
    if session.get("role") != "resident":
        return redirect(url_for("login"))
    
    try:
        content = request.form.get("content", "").strip()
        if not content:
            return redirect(url_for("post_detail", post_id=post_id))
        
        username = session.get("username", "Anonymous")
        author_apt = session.get("apartment_number", "")
        comment_data = {
            "post_id": post_id,
            "author": username,
            "author_apt": author_apt,
            "content": content,
            "created_at": datetime.now()
        }
        
        db.comments.insert_one(comment_data)
        return redirect(url_for("post_detail", post_id=post_id))
    except:
        return redirect(url_for("community"))


@app.route("/community/post/<post_id>/delete", methods=["POST"])
def delete_post(post_id):
    if session.get("role") != "resident":
        return redirect(url_for("login"))
    
    try:
        post = db.community_posts.find_one({"_id": ObjectId(post_id)})
        if not post:
            return redirect(url_for("community"))
        
        username = session.get("username", "")
        post_author = post.get("author", "")
        if post_author.lower() != username.lower() and username.lower() not in post_author.lower():
            return redirect(url_for("post_detail", post_id=post_id))
        
        if post.get("image_url"):
            image_path = post["image_url"].replace("/static/", "static/")
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.community_posts.delete_one({"_id": ObjectId(post_id)})
        db.comments.delete_many({"post_id": post_id})
        
        return redirect(url_for("community"))
    except:
        return redirect(url_for("community"))


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
        apartment_number = request.form.get("apartment_number", "").strip().upper()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        role = request.form.get("role", "")

        if not first_name or not last_name or not apartment_number or not username or not password or not role:
            error = "All fields are required."
        elif len(username) < 3:
            error = "Username must be at least 3 characters."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif role not in ["admin", "resident"]:
            error = "Invalid role selected."
        elif db is not None:
            existing_user = db.users.find_one({"username": username})
            if existing_user:
                error = "Username already exists. Please choose another."
            else:
                try:
                    hashed_pw = generate_password_hash(password)
                    db.users.insert_one({
                        "first_name": first_name,
                        "last_name": last_name,
                        "apartment_number": apartment_number,
                        "username": username,
                        "password": hashed_pw,
                        "role": role
                    })
                    session["username"] = username
                    session["first_name"] = first_name
                    session["apartment_number"] = apartment_number
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
        elif db is not None:
            try:
                user = db.users.find_one({"username": username})
                if user and check_password_hash(user["password"], password):
                    session["username"] = username
                    session["first_name"] = user.get("first_name", "User")
                    session["apartment_number"] = user.get("apartment_number", "")
                    session["role"] = user["role"]
                    if user["role"] == "admin":
                        return redirect(url_for("admin_dashboard"))
                    else:
                        return redirect(url_for("dashboard"))
                else:
                    error = "Invalid username or password."
            except Exception as e:
                print(f"Error during login: {e}")
                error = "An error occurred. Please try again."
        else:
            error = "Database connection failed. Please try again later."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/test_mongo")
def test_mongo():
    if db is None:
        return "MongoDB not connected", 500
    try:
        collections = db.list_collection_names()
        return f"MongoDB OK! Collections: {collections}"
    except Exception as e:
        return f"MongoDB error: {e}", 500


def print_routes():
    for rule in app.url_map.iter_rules():
        print(rule, "->", rule.endpoint)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
