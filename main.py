# general imports
import os
from flask import Flask, request, session, redirect, url_for, render_template
from functools import wraps # preserves function metadata
from flask_sqlalchemy import SQLAlchemy

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