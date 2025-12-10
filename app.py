import os
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = "hanqi"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.after_request
def set_no_cache(response):
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    return response

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://gz:1234@cluster0.fv25oph.mongodb.net/?appName=Cluster0")
MONGODB_DB = os.getenv("MONGODB_DB", "smart_apartment_db")

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    db = client[MONGODB_DB]
    client.admin.command("ping")
    print("MongoDB connected successfully")
    
    db.sensor_readings.create_index([("apartment_id", 1), ("room", 1), ("sensor_type", 1), ("timestamp", -1)])
    db.sensor_readings.create_index([("timestamp", -1)])
    print("MongoDB indexes ensured")
except Exception as e:
    print(f"MongoDB connection failed: {e}")
    db = None
    client = None

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_objectid_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_objectid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid_to_str(item) for item in obj]
    else:
        return obj


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
        except Exception:
            pass

    alerts = []
    sensor = None
    maintenance_requests = []
    pending_count = 0

    if db is not None:
        try:
            alerts = list(db.alerts.find({"status": "new"}))

            apartment_id = session.get("apartment_number", "")
            latest_docs = []
            if apartment_id:
                latest_docs = list(
                    db.sensor_readings.find({"apartment_id": apartment_id})
                    .sort("timestamp", -1)
                    .limit(200)
                )

            latest_by_type = {}
            for d in latest_docs:
                st = d.get("sensor_type")
                if st and st not in latest_by_type:
                    latest_by_type[st] = d
                if len(latest_by_type) >= 4:
                    break

            if apartment_id:
                sensor = {
                    "apartment_id": apartment_id,
                    "temperature": latest_by_type.get("temperature", {}).get("value"),
                    "smoke": latest_by_type.get("smoke", {}).get("value"),
                    "noise": latest_by_type.get("noise", {}).get("value"),
                    "motion": latest_by_type.get("motion", {}).get("value"),
                    "timestamp": latest_docs[0].get("timestamp") if latest_docs else None,
                }
            else:
                sensor = None

            username = session.get("username", "")
            apartment_number = session.get("apartment_number", "")

            query_conditions = [{"resident_username": username}]
            if apartment_number:
                query_conditions.append({"apartment_number": apartment_number})

            all_pending = list(
                db.maintenance_requests.find(
                    {"$or": query_conditions, "status": {"$ne": "resolved"}}
                ).sort("created_at", -1)
            )

            maintenance_requests = all_pending[:1] if all_pending else []
            pending_count = len(all_pending)

        except Exception as e:
            print(f"Error loading dashboard data: {e}")
            alerts = []
            sensor = None
            maintenance_requests = []
            pending_count = 0

    current_date = datetime.now()
    date_str = current_date.strftime("%A, %B %d")

    return render_template(
        "resident/dashboard.html",
        alerts=alerts,
        sensor_data=sensor,
        maintenance_requests=maintenance_requests,
        pending_count=pending_count,
        current_date=date_str,
    )


@app.route("/packages")
def packages():
    if "username" not in session or session.get("role") != "resident":
        return redirect(url_for("login"))
    
    pkgs = []
    if db is not None:
        try:
            username = session.get("username", "")
            apartment_number = session.get("apartment_number", "")
            first_name = session.get("first_name", "")
            
            query_conditions = [
                {"resident_username": username}
            ]
            
            if apartment_number:
                query_conditions.append({"apartment_number": apartment_number})
            
            if first_name:
                query_conditions.append({"resident_name": {"$regex": f"^{first_name}", "$options": "i"}})
            
            full_name = f"{first_name} {session.get('last_name', '')}".strip()
            if full_name and " " in full_name:
                query_conditions.append({"resident_name": {"$regex": full_name.replace(" ", ".*"), "$options": "i"}})
            
            query = {"$or": query_conditions}
            pkgs_raw = list(db.packages.find(query).sort("arrived_at", -1))
            for pkg in pkgs_raw:
                pkg["_id"] = str(pkg["_id"])
                status = pkg.get("status", "arrived")
                if status == "arrived" or status == "notified":
                    pkg["status"] = "ready"
                elif status == "picked_up":
                    pkg["status"] = "picked_up"
                else:
                    pkg["status"] = "processing"
                
                if "arrived_at" in pkg and pkg["arrived_at"]:
                    if isinstance(pkg["arrived_at"], datetime):
                        now = datetime.now()
                        time_diff = (now - pkg["arrived_at"]).total_seconds()
                        if time_diff < 86400:
                            pkg["arrival"] = "Yesterday"
                        elif time_diff < 172800:
                            pkg["arrival"] = f"{int(time_diff / 86400)} days ago"
                        else:
                            pkg["arrival"] = pkg["arrived_at"].strftime("%b %d")
                    else:
                        pkg["arrival"] = str(pkg["arrived_at"])
                else:
                    pkg["arrival"] = "Unknown"
                
                if not pkg.get("tracking"):
                    pkg["tracking"] = f"#{pkg['_id'][:8].upper()}"
                
                pkgs.append(pkg)
        except Exception as e:
            print(f"Error loading packages: {e}")
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


@app.route("/maintenance/new", methods=["GET", "POST"])
def maintenance():
    if "username" not in session or session.get("role") != "resident":
        return redirect(url_for("login"))
    
    if request.method == "POST":
        if db is None:
            return render_template("resident/maintenance.html", error="Database unavailable")
        
        try:
            category = request.form.get("category", "").strip()
            description = request.form.get("description", "").strip()
            urgency = request.form.get("urgency", "normal").strip()
            entry_permit = request.form.get("entry_permit") == "1"
            
            if not category or not description:
                return render_template("resident/maintenance.html", error="Category and description are required.")
            
            username = session.get("username", "")
            first_name = session.get("first_name", "")
            last_name = session.get("last_name", "")
            apartment_number = session.get("apartment_number", "")
            
            if db is not None:
                try:
                    user = db.users.find_one({"username": username})
                    if user:
                        first_name = user.get("first_name", first_name)
                        last_name = user.get("last_name", last_name)
                        apartment_number = user.get("apartment_number", apartment_number)
                except:
                    pass
            
            maintenance_data = {
                "apartment_number": apartment_number,
                "resident_name": f"{first_name} {last_name}".strip(),
                "resident_username": username,
                "category": category,
                "description": description,
                "urgency": urgency,
                "entry_permit": entry_permit,
                "status": "pending",
                "created_at": datetime.now()
            }
            
            result = db.maintenance_requests.insert_one(maintenance_data)
            
            return render_template("resident/maintenance_success.html")
        except Exception as e:
            print(f"Error creating maintenance request: {e}")
            return render_template("resident/maintenance.html", error="Could not submit request")
    
    return render_template("resident/maintenance.html")


@app.route("/admin")
def admin_dashboard():
    if "username" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template("admin/admin.html")


@app.route("/api/admin/packages", methods=["GET", "POST"])
def admin_packages():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    if request.method == "GET":
        status = request.args.get("status", "").strip()
        query = {}
        if status:
            query["status"] = status
        
        packages = []
        if db is not None:
            try:
                packages = list(db.packages.find(query).sort("arrived_at", -1))
                for pkg in packages:
                    pkg["_id"] = str(pkg["_id"])
                    pkg["package_id"] = str(pkg["_id"])
                    if "apartment_number" in pkg:
                        pkg["apartment_id"] = pkg["apartment_number"]
                    if "arrived_at" in pkg and pkg["arrived_at"]:
                        if isinstance(pkg["arrived_at"], datetime):
                            pkg["arrived_at"] = pkg["arrived_at"].isoformat()
            except Exception as e:
                print(f"Error loading packages: {e}")
        
        return jsonify({"data": packages})
    
    elif request.method == "POST":
        if db is None:
            return jsonify({"error": "Database unavailable"}), 500
        
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "Missing data"}), 400
            
            resident_id = data.get("resident_id", "").strip()
            carrier = data.get("carrier", "").strip()
            location = data.get("location", "").strip()
            
            if not resident_id or not carrier or not location:
                return jsonify({"error": "Fill all fields"}), 400
            
            user = None
            if db is not None:
                try:
                    name_parts = resident_id.split()
                    query_conditions = [
                        {"username": resident_id},
                        {"apartment_number": resident_id.upper()}
                    ]
                    
                    if len(name_parts) >= 2:
                        query_conditions.append({
                            "$and": [
                                {"first_name": {"$regex": f"^{name_parts[0]}", "$options": "i"}},
                                {"last_name": {"$regex": f"^{name_parts[-1]}", "$options": "i"}}
                            ]
                        })
                    elif len(name_parts) == 1:
                        query_conditions.extend([
                            {"first_name": {"$regex": f"^{name_parts[0]}", "$options": "i"}},
                            {"last_name": {"$regex": f"^{name_parts[0]}", "$options": "i"}}
                        ])
                    
                    user = db.users.find_one({"$or": query_conditions})
                except Exception as e:
                    return jsonify({"error": "Could not search for resident"}), 500
            
            if not user:
                return jsonify({"error": f"Could not find resident '{resident_id}'"}), 404
            
            resident_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            apartment_number = user.get("apartment_number", "").strip().upper() if user.get("apartment_number") else ""
            
            package_data = {
                "resident_username": user.get("username", ""),
                "resident_name": resident_name,
                "apartment_number": apartment_number,
                "carrier": carrier,
                "location": location,
                "status": "arrived",
                "arrived_at": datetime.now(),
                "created_at": datetime.now()
            }
            
            result = db.packages.insert_one(package_data)
            return jsonify({"success": True, "package_id": str(result.inserted_id)}), 201
        except Exception as e:
            print(f"Error creating package: {e}")
            return jsonify({"error": "Could not create package"}), 500


@app.route("/api/admin/packages/<package_id>", methods=["PATCH", "DELETE"])
def update_package_status(package_id):
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        if request.method == "PATCH":
            data = request.get_json()
            new_status = data.get("status", "").strip()
            
            if new_status not in ["arrived", "notified", "picked_up"]:
                return jsonify({"error": "Invalid status"}), 400
            
            result = db.packages.update_one(
                {"_id": ObjectId(package_id)},
                {"$set": {"status": new_status}}
            )
            
            if result.matched_count == 0:
                return jsonify({"error": "Package not found"}), 404
            
            return jsonify({"success": True})
        
        elif request.method == "DELETE":
            result = db.packages.delete_one({"_id": ObjectId(package_id)})
            
            if result.deleted_count == 0:
                return jsonify({"error": "Package not found"}), 404
            
            return jsonify({"success": True})
    except Exception as e:
        print(f"Error managing package: {e}")
        return jsonify({"error": "Failed to manage package"}), 500


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
                    session.permanent = True
                    session["username"] = username
                    session["first_name"] = first_name
                    session["apartment_number"] = apartment_number
                    session["role"] = role
                    if role == "admin":
                        return redirect(url_for("admin_dashboard"))
                    return redirect(url_for("dashboard"))
                except:
                    error = "Something went wrong"
        else:
            error = "Database unavailable"

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
                    session.permanent = True
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
                error = "Login failed"
        else:
            error = "Database unavailable"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/api/sensor_readings/latest", methods=["GET"])
def api_latest_sensor_readings():
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500

    limit = int(request.args.get("limit", 50))
    docs = list(db.sensor_readings.find({}).sort("timestamp", -1).limit(limit))

    for d in docs:
        d["_id"] = str(d["_id"])
        if isinstance(d.get("timestamp"), datetime):
            d["timestamp"] = d["timestamp"].isoformat()

    return jsonify({"data": docs})


@app.route("/api/admin/overview")
def admin_overview():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        alerts_today = list(db.alerts.find({"status": "new"}))
        open_alerts = list(db.alerts.find({"status": {"$in": ["new", "open"]}}))
        maintenance = list(db.maintenance_requests.find({"status": {"$ne": "resolved"}}))
        unpicked_packages = list(db.packages.find({"status": {"$ne": "picked_up"}}))
        
        print(f"Admin overview - alerts_today: {len(alerts_today)}, open_alerts: {len(open_alerts)}, maintenance: {len(maintenance)}, packages: {len(unpicked_packages)}")
        
        recent_alerts_query = db.alerts.find()
        recent_alerts_query = recent_alerts_query.sort("timestamp", -1)
        recent_alerts = list(recent_alerts_query.limit(5))
        recent_maintenance = list(db.maintenance_requests.find().sort("created_at", -1).limit(5))
        
        print(f"Admin overview - recent_alerts: {len(recent_alerts)}, recent_maintenance: {len(recent_maintenance)}")
        
        for alert in recent_alerts:
            alert["_id"] = str(alert["_id"])
            alert["alert_id"] = str(alert["_id"])
            if "reading_id" in alert:
                alert["reading_id"] = str(alert["reading_id"])
            if "timestamp" in alert and isinstance(alert["timestamp"], datetime):
                alert["created_at"] = alert["timestamp"].isoformat()
            elif "created_at" in alert and isinstance(alert["created_at"], datetime):
                alert["created_at"] = alert["created_at"].isoformat()
            if "room" in alert and "room_id" not in alert:
                alert["room_id"] = alert["room"]
        
        for req in recent_maintenance:
            req["_id"] = str(req["_id"])
            req["request_id"] = str(req["_id"])
            if "apartment_number" in req:
                req["apartment_id"] = req["apartment_number"]
            if "created_at" in req and isinstance(req["created_at"], datetime):
                req["created_at"] = req["created_at"].isoformat()
        
        response_data = {
            "data": {
                "counts": {
                    "alerts_total_today": len(alerts_today),
                    "alerts_unresolved": len(open_alerts),
                    "maintenance_open": len(maintenance),
                    "packages_unpicked": len(unpicked_packages)
                },
                "recent_alerts": convert_objectid_to_str(recent_alerts),
                "recent_maintenance": convert_objectid_to_str(recent_maintenance)
            }
        }
        
        return jsonify(response_data)
    except Exception as e:
        import traceback
        print(f"Error loading overview: {e}")
        print(traceback.format_exc())
        return jsonify({"error": f"Failed to load overview: {str(e)}"}), 500


@app.route("/api/admin/alerts", methods=["GET", "DELETE"])
def admin_alerts():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        if request.method == "DELETE":
            try:
                result = db.alerts.delete_many({})
                return jsonify({"message": f"Deleted {result.deleted_count} alerts successfully", "deleted_count": result.deleted_count})
            except Exception as delete_error:
                print(f"Error deleting alerts: {delete_error}")
                import traceback
                traceback.print_exc()
                return jsonify({"error": f"Failed to delete alerts: {str(delete_error)}"}), 500
        
        elif request.method == "GET":
            severity = request.args.get("severity", "").strip()
            status = request.args.get("status", "").strip()
            
            query = {}
            if severity:
                query["severity"] = severity
            if status:
                query["status"] = status
            
            alerts_query = db.alerts.find(query)
            alerts_query = alerts_query.sort("timestamp", -1)
            alerts = list(alerts_query)
            for alert in alerts:
                alert["_id"] = str(alert["_id"])
                alert["alert_id"] = str(alert["_id"])
                if "reading_id" in alert:
                    alert["reading_id"] = str(alert["reading_id"])
                if "timestamp" in alert and isinstance(alert["timestamp"], datetime):
                    alert["created_at"] = alert["timestamp"].isoformat()
                elif "created_at" in alert and isinstance(alert["created_at"], datetime):
                    alert["created_at"] = alert["created_at"].isoformat()
                if "room" in alert and "room_id" not in alert:
                    alert["room_id"] = alert["room"]
            
            return jsonify({"data": convert_objectid_to_str(alerts)})
    except Exception as e:
        print(f"Error in alerts API: {e}")
        import traceback
        traceback.print_exc()
        error_msg = str(e) if str(e) else "Failed to process request"
        return jsonify({"error": error_msg}), 500


@app.route("/api/admin/alerts/<alert_id>", methods=["PATCH", "DELETE"])
def update_alert_status(alert_id):
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        if request.method == "DELETE":
            result = db.alerts.delete_one({"_id": ObjectId(alert_id)})
            if result.deleted_count == 0:
                return jsonify({"error": "Alert not found"}), 404
            return jsonify({"message": "Alert deleted successfully"})
        
        elif request.method == "PATCH":
            data = request.get_json()
            new_status = data.get("status", "").strip()
            
            if new_status not in ["open", "resolved", "ignored"]:
                return jsonify({"error": "Invalid status"}), 400
            
            result = db.alerts.update_one(
                {"_id": ObjectId(alert_id)},
                {"$set": {"status": new_status}}
            )
            
            if not result or result.matched_count == 0:
                return jsonify({"error": "Alert not found"}), 404
            
            return jsonify({"success": True})
    except Exception as e:
        print(f"Error updating alert: {e}")
        return jsonify({"error": "Failed to update alert"}), 500


@app.route("/api/admin/maintenance", methods=["GET"])
def admin_maintenance():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        status = request.args.get("status", "").strip()
        
        query = {}
        if status:
            query["status"] = status
        
        requests = list(db.maintenance_requests.find(query).sort("created_at", -1))
        
        for req in requests:
            req["_id"] = str(req["_id"])
            req["request_id"] = str(req["_id"])
            if "apartment_number" in req:
                req["apartment_id"] = req["apartment_number"]
            if "created_at" in req and isinstance(req["created_at"], datetime):
                req["created_at"] = req["created_at"].isoformat()
        
        return jsonify({"data": requests})
    except Exception as e:
        print(f"Error loading maintenance: {e}")
        return jsonify({"error": "Failed to load maintenance"}), 500


@app.route("/api/admin/maintenance/<request_id>", methods=["PATCH"])
def update_maintenance_status(request_id):
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        data = request.get_json()
        new_status = data.get("status", "").strip()
        
        if new_status not in ["pending", "in_progress", "resolved"]:
            return jsonify({"error": "Invalid status"}), 400
        
        result = db.maintenance_requests.update_one(
            {"_id": ObjectId(request_id)},
            {"$set": {"status": new_status}}
        )
        
        if result.matched_count == 0:
            return jsonify({"error": "Maintenance request not found"}), 404
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Error updating maintenance: {e}")
        return jsonify({"error": "Failed to update maintenance"}), 500


@app.route("/api/admin/rooms", methods=["GET"])
def admin_rooms():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        response = None
        rooms_list = []
        
        rooms_from_db = list(db.rooms.find())
        print(f"Admin rooms - found {len(rooms_from_db)} rooms in db.rooms collection")
        if rooms_from_db:
            for room in rooms_from_db:
                room_id_str = str(room["_id"])
                room_data = {
                    "_id": room_id_str,
                    "room_id": room_id_str,
                    "apartment_id": room.get("apartment_id", room.get("apartment", "")),
                    "room_name": room.get("room_name", room.get("room", ""))
                }
                
                latest_reading = db.sensor_readings.find_one(
                    {"room_id": room.get("room_id") or room.get("_id")},
                    sort=[("timestamp", -1)]
                )
                
                if latest_reading:
                    room_data["latest_readings"] = {
                        "temperature": {
                            "timestamp": latest_reading.get("timestamp").isoformat() if isinstance(latest_reading.get("timestamp"), datetime) else str(latest_reading.get("timestamp", "")),
                            "value": latest_reading.get("temperature", latest_reading.get("value", 0))
                        }
                    }
                
                rooms_list.append(convert_objectid_to_str(room_data))
        else:
            sensor_readings_count = db.sensor_readings.count_documents({})
            print(f"Admin rooms - found {sensor_readings_count} sensor_readings in database")
            
            try:
                unique_rooms = list(db.sensor_readings.aggregate([
                    {"$match": {
                        "apartment_id": {"$regex": "^A-[0-9]+$"}
                    }},
                    {"$group": {
                        "_id": {
                            "apartment_id": "$apartment_id",
                            "room": "$room"
                        }
                    }},
                    {"$sort": {"_id.apartment_id": 1, "_id.room": 1}}
                ]))
                print(f"Admin rooms - aggregated {len(unique_rooms)} unique rooms from sensor_readings (new format only)")
                if unique_rooms:
                    sample_ids = [f"{r['_id'].get('apartment_id')}_{r['_id'].get('room')}" for r in unique_rooms[:5]]
                    print(f"Admin rooms - Sample room IDs: {sample_ids}")
            except Exception as agg_error:
                print(f"Admin rooms - aggregation error: {agg_error}")
                unique_rooms = []
            
            for room_group in unique_rooms:
                apartment_id = room_group["_id"].get("apartment_id", "")
                room_name = room_group["_id"].get("room", "")
                
                if not apartment_id or not room_name:
                    continue
                
                room_id = f"{apartment_id}_{room_name}".replace(" ", "_")
                
                all_sensor_readings = list(db.sensor_readings.find(
                    {"apartment_id": apartment_id, "room": room_name}
                ).sort([("timestamp", -1), ("_id", -1)]).limit(50))
                
                if not all_sensor_readings or len(all_sensor_readings) == 0:
                    continue
                
                latest_timestamp_in_query = all_sensor_readings[0].get("timestamp")
                if latest_timestamp_in_query:
                    from datetime import timedelta
                    if isinstance(latest_timestamp_in_query, datetime):
                        now_utc = datetime.now(timezone.utc)
                        ts_utc = latest_timestamp_in_query
                        if ts_utc.tzinfo is None:
                            ts_utc = ts_utc.replace(tzinfo=timezone.utc)
                        time_diff = now_utc - ts_utc
                        if time_diff > timedelta(minutes=5):
                            print(f"Skipping {room_id}: data too old ({time_diff}), latest: {latest_timestamp_in_query}")
                            continue
                
                room_data = {
                    "room_id": room_id,
                    "apartment_id": apartment_id,
                    "room_name": room_name
                }
                
                latest_readings = {}
                latest_timestamp = None
                
                if all_sensor_readings and room_id == "1A_room-1":
                    print(f"Debug {room_id}: Query filter: apartment_id='{apartment_id}', room='{room_name}'")
                    print(f"Debug {room_id}: Found {len(all_sensor_readings)} readings, first timestamp: {all_sensor_readings[0].get('timestamp')}")
                    if len(all_sensor_readings) > 0:
                        sample = all_sensor_readings[0]
                        print(f"Debug {room_id}: Sample reading - apartment_id='{sample.get('apartment_id')}', room='{sample.get('room')}', timestamp={sample.get('timestamp')}")
                    
                    latest_in_db = db.sensor_readings.find_one({}, sort=[("timestamp", -1), ("_id", -1)])
                    if latest_in_db:
                        print(f"Debug {room_id}: Latest in entire DB - apartment_id='{latest_in_db.get('apartment_id')}', room='{latest_in_db.get('room')}', timestamp={latest_in_db.get('timestamp')}")
                
                readings_by_type = {}
                for reading in all_sensor_readings:
                    sensor_type = reading.get("sensor_type")
                    if sensor_type and sensor_type not in readings_by_type:
                        readings_by_type[sensor_type] = reading
                
                for sensor_type in ["temperature", "smoke", "noise", "motion"]:
                    if sensor_type in readings_by_type:
                        latest_reading = readings_by_type[sensor_type]
                        timestamp = latest_reading.get("timestamp")
                        value = latest_reading.get("value", 0)
                        if timestamp:
                            if latest_timestamp is None or timestamp > latest_timestamp:
                                latest_timestamp = timestamp
                            if isinstance(timestamp, datetime):
                                timestamp_str = timestamp.isoformat()
                            else:
                                timestamp_str = str(timestamp)
                            latest_readings[sensor_type] = {
                                "timestamp": timestamp_str,
                                "value": value
                            }
                
                if latest_readings:
                    if latest_timestamp and isinstance(latest_timestamp, datetime):
                        latest_timestamp_str = latest_timestamp.isoformat()
                    else:
                        latest_timestamp_str = str(latest_timestamp) if latest_timestamp else ""
                    
                    for sensor_type in latest_readings:
                        latest_readings[sensor_type]["timestamp"] = latest_timestamp_str
                    
                    room_data["latest_readings"] = latest_readings
                
                rooms_list.append(convert_objectid_to_str(room_data))
        
        print(f"Admin rooms - found {len(rooms_list)} rooms")
        if rooms_list:
            first_room = rooms_list[0]
            if "latest_readings" in first_room and first_room["latest_readings"]:
                temp_info = first_room["latest_readings"].get("temperature", {})
                from datetime import datetime as dt_now
                now_str = dt_now.utcnow().isoformat()
                print(f"Admin rooms - Current time: {now_str}, Sample room {first_room.get('room_id')} latest temp: {temp_info.get('value')} at {temp_info.get('timestamp')}")
                
                total_count = db.sensor_readings.count_documents({})
                latest_overall = db.sensor_readings.find_one({}, sort=[("timestamp", -1), ("_id", -1)])
                if latest_overall:
                    print(f"Admin rooms - DB total: {total_count}, Latest overall timestamp: {latest_overall.get('timestamp')}")
        return jsonify({"data": rooms_list})
    except Exception as e:
        print(f"Error loading rooms: {e}")
        return jsonify({"error": "Failed to load rooms"}), 500


@app.route("/api/admin/rooms/<room_id>/history", methods=["GET"])
def admin_room_history(room_id):
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        room_parts = room_id.rsplit("_", 1)
        if len(room_parts) == 2:
            apartment_id, room_name = room_parts
            room_name = room_name.replace("_", " ")
        else:
            return jsonify({"error": "Invalid room_id format"}), 400
        
        all_readings = list(db.sensor_readings.find(
            {"apartment_id": apartment_id, "room": room_name}
        ).sort([("timestamp", -1), ("_id", -1)]).limit(100))
        
        readings_by_timestamp = {}
        for reading in all_readings:
            timestamp = reading.get("timestamp")
            if isinstance(timestamp, datetime):
                timestamp_key = timestamp.isoformat()
            else:
                timestamp_key = str(timestamp) if timestamp else ""
            
            if timestamp_key not in readings_by_timestamp:
                readings_by_timestamp[timestamp_key] = {
                    "timestamp": timestamp_key,
                    "temperature": None,
                    "smoke": None,
                    "noise": None,
                    "motion": None
                }
            
            sensor_type = reading.get("sensor_type", "")
            value = reading.get("value", 0)
            
            if sensor_type == "temperature":
                readings_by_timestamp[timestamp_key]["temperature"] = value
            elif sensor_type == "smoke":
                readings_by_timestamp[timestamp_key]["smoke"] = value
            elif sensor_type == "noise":
                readings_by_timestamp[timestamp_key]["noise"] = value
            elif sensor_type == "motion":
                readings_by_timestamp[timestamp_key]["motion"] = bool(value)
        
        history = list(readings_by_timestamp.values())
        history.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return jsonify({"data": {"readings": convert_objectid_to_str(history)}})
    except Exception as e:
        print(f"Error loading room history: {e}")
        return jsonify({"error": "Failed to load room history"}), 500


@app.route("/api/admin/community/posts", methods=["GET"])
def admin_community_posts():
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        status = request.args.get("status", "").strip()
        category = request.args.get("category", "").strip()
        
        query = {}
        if status:
            if status == "active":
                query["status"] = {"$in": ["available", "active"]}
            elif status == "closed":
                query["status"] = "closed"
            else:
                query["status"] = status
        if category:
            query["category"] = category
        
        posts = list(db.community_posts.find(query).sort("created_at", -1))
        
        for post in posts:
            post["_id"] = str(post["_id"])
            post["post_id"] = str(post["_id"])
            if "author" in post:
                post["resident_name"] = post.get("author", "")
            if "status" not in post or post["status"] == "available":
                post["status"] = "active"
            if "created_at" in post and isinstance(post["created_at"], datetime):
                post["created_at"] = post["created_at"].isoformat()
        
        return jsonify({"data": posts})
    except Exception as e:
        print(f"Error loading community posts: {e}")
        return jsonify({"error": "Failed to load community posts"}), 500


@app.route("/api/admin/community/posts/<post_id>", methods=["PATCH", "DELETE"])
def admin_community_post(post_id):
    if "username" not in session or session.get("role") != "admin":
        return jsonify({"error": "Unauthorized"}), 401
    
    if db is None:
        return jsonify({"error": "Database unavailable"}), 500
    
    try:
        if request.method == "PATCH":
            data = request.get_json()
            new_status = data.get("status", "").strip()
            
            if new_status not in ["active", "closed"]:
                return jsonify({"error": "Invalid status"}), 400
            
            result = db.community_posts.update_one(
                {"_id": ObjectId(post_id)},
                {"$set": {"status": new_status}}
            )
            
            if result.matched_count == 0:
                return jsonify({"error": "Post not found"}), 404
            
            return jsonify({"success": True})
        
        elif request.method == "DELETE":
            post = db.community_posts.find_one({"_id": ObjectId(post_id)})
            if not post:
                return jsonify({"error": "Post not found"}), 404
            
            if post.get("image_url"):
                image_path = post["image_url"].replace("/static/", "static/")
                if os.path.exists(image_path):
                    os.remove(image_path)
            
            db.community_posts.delete_one({"_id": ObjectId(post_id)})
            db.comments.delete_many({"post_id": post_id})
            
            return jsonify({"success": True})
    except Exception as e:
        print(f"Error managing community post: {e}")
        return jsonify({"error": "Failed to manage post"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
