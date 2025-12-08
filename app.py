from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "hanqi"

@app.route("/")
def index():
    role = session.get("role")
    if role == "admin":
        return redirect(url_for("admin_dashboard"))
    elif role == "resident":
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route('/dashboard')
def dashboard():
    if session.get("role") != "resident":
        return redirect(url_for("login"))
    return render_template('resident/dashboard.html')

@app.route('/packages')
def packages():
    return render_template('resident/packages.html')

@app.route('/community')
def community():
    return render_template('resident/community.html')

@app.route('/community/create')
def create_post():
    return render_template('resident/create_post.html')

@app.route('/community/post/<int:post_id>')
def post_detail(post_id):
    return render_template('resident/post_detail.html', post_id=post_id)

@app.route('/maintenance/new')
def maintenance():
    return render_template('resident/maintenance.html')

@app.route('/admin')
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template('admin/admin.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")

        if password == "admin123":
            session["role"] = "admin"
            return redirect(url_for("admin_dashboard"))
        elif password == "resident123":
            session["role"] = "resident"
            return redirect(url_for("dashboard")) 
        else:
            error = "Invalid password. Try admin123 or resident123."

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))




if __name__ == '__main__':
    app.run(debug=True, port=5001)