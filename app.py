from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('resident/dashboard.html')

@app.route('/dashboard')
def dashboard():
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

if __name__ == '__main__':
    app.run(debug=True, port=5001)