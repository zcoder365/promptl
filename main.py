# general imports
import os
from flask import Flask, request, session, redirect, url_for, render_template, flash
from functools import wraps # preserves function metadata
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# import other files
from utils.accounts import *
from utils.prompts import *

# create the flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_URI') # get the URI for the database
db = SQLAlchemy(app) # set up the SQLAlchemy database

# create user database
class User(db.Model):
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# create stories database
class Story(db.Model):
    title = db.Column(db.String(100), unique=True, nullable=False)
    story_content = db.Column(db.String(800), nullable=False)
    author = db.Column(db.String(80), nullable=False)

# create all of the databases
with app.app_context():
    db.create_all()

# login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# page when the user comes to promptl
@app.route('/')
def index():
    return render_template('signup.html')

# home page route
@app.route('/home')
def home():
    # generate the prompts
    prps = gen_all_prompts()
    
    # allocate each prompt to a variable
    name = prps['name']
    job = prps['job']
    place = prps['place']
    object = prps['object']
    bonus = prps['bonus']

    # return the main page for writing with the prompts
    return render_template('index.html', name=name, job=job, object=object, place=place, bonus=bonus)

# generate a new prompt
@app.route('/new-prompt')
def new_prompt():
    # reload the page to get a new 5 prompts
    return redirect(url_for("home"))

# about page
@app.route('/about')
def about_page():
    # return the page about the game
    return render_template('about.html')

# let the user signup
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        # get username and password
        username = request.form["username"]
        password = request.form["password"]
        
        # hash the password
        hashed_pw = generate_password_hash(request.form['password'])
        
        # create the user
        user = User(username=request.form['username'], password=hashed_pw)
        
        # add the user to the database and save the changes
        db.session.add(user)
        db.session.commit()
        
        # return the login page so the user can log in
        return redirect(url_for("login"))
    
    # if GET request, just show signup page
    return render_template("signup.html")

# login route
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        # get username and password from the form
        username = request.form["username"]
        password = request.form["password"]
        
        # find the user in the database
        user = User.query.filter_by(username=request.form['username']).first()
        
        # if the user exists and the passwords match, create the session with the user id
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect(url_for("index"))

        # flash error message for incorrect username or password
        flash("Invalid username or password.")
    
    # if GET request, just show the login page
    return render_template("login.html")

# logout route
@app.route('/logout')
def logout():
    # clear the session
    session.pop('user_id', None)
    return redirect('/login') # redirect to login page

# mainloop
if __name__ == "__main__":
    app.run(port=8080, debug=True)