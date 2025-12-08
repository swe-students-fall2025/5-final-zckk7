"""Main web app module"""

from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient


app = Flask(__name__)
app.secret_key = "hanqi"

MONGO_URI = "mongodb+srv://gz:1234@cluster0.fv25oph.mongodb.net/?appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client.smart_apartment_db


@app.route("/")
def index():
    """Redirect users to the correct dashboard."""
    role = session.get("role")
    if role == "admin":
        return redirect(url_for("admin_dashboard"))
    if role == "resident":
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    """Render the resident dashboard."""
    if session.get("role") != "resident":
        return redirect(url_for("login"))
    active_alerts = list(db.alerts.find({"status": "new"}))
    return render_template("resident/dashboard.html", alerts=active_alerts)


@app.route("/packages")
def packages():
    """Render the packages page."""
    return render_template("resident/packages.html")


@app.route("/community")
def community():
    """Render the main community feed."""
    return render_template("resident/community.html")


@app.route("/community/create")
def create_post():
    """Render the page to create a new community post."""
    return render_template("resident/create_post.html")


@app.route("/community/post/<int:post_id>")
def post_detail(post_id):
    """Render the details of a specific community post."""
    return render_template("resident/post_detail.html", post_id=post_id)


@app.route("/maintenance/new")
def maintenance():
    """Render the maintenance request form."""
    return render_template("resident/maintenance.html")


@app.route("/admin")
def admin_dashboard():
    """Render the admin dashboard."""
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template("admin/admin.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")

        if password == "admin123":
            session["role"] = "admin"
            return redirect(url_for("admin_dashboard"))
        if password == "resident123":
            session["role"] = "resident"
            return redirect(url_for("dashboard"))

        error = "Invalid password. Try admin123 or resident123."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """Log the user out."""
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
