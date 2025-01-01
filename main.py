# general imports
import os
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, request, session, redirect, url_for, render_template, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

# import other files
from utils.prompts import *
from utils.model import *

# load the .env file
load_dotenv()

# create the flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = "key"
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI') # get the URI for the database
db = SQLAlchemy(app) # set up the SQLAlchemy database

# create user database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    points = db.Column(db.Integer, default=0)
    total_word_count = db.Column(db.Integer, default=0) # keep track of total word count for the user
    stories = relationship("Story", back_populates="author")

# create stories database
class Story(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    story_content = db.Column(db.String(800), nullable=False)
    word_count = db.Column(db.Integer, nullable=False)
    prompt = db.Column(db.String(100), nullable=False)
    author = relationship("User", back_populates="stories")
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# create all of the databases
with app.app_context():
    db.create_all()
    
# GLOBAL VARIABLES
prps = gen_all_prompts() # generate the prompts

# login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for('login'))
        # return f(*args, **kwargs)
    return decorated_function

# page when the user comes to promptl
@app.route('/')
def index():
    return render_template('signup.html')

# home page route
@app.route('/home')
def home():
    # regenerate the prompts if the page is reloaded
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
        
        # check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template("signup.html", message="Username already exists.")
        
        try:
            # hash the password
            hashed_pw = generate_password_hash(password)
            
            # create the user
            user = User(username=username, password=hashed_pw, points=0, total_word_count=0)
            
            # add the user to the database and save the changes
            db.session.add(user)
            db.session.commit()
            
            # return the login page so the user can log in
            return redirect(url_for("login"))
        
        except Exception as e:
            # rollback the session in case of any other errors
            db.session.rollback()
            return render_template("signup.html", message="An error occurred during signup.")
    
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
        user = User.query.filter_by(username=username).first()
        
        # if the user exists and the passwords match, create the session with the user id
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect("/home")

        # return error message if the user doesn't exist or the passwords don't match
        return "Invalid username or password."
    
    # if GET request, just show the login page
    return render_template("login.html")

# logout route
@app.route('/logout')
def logout():
    session.clear() # clear the session
    return redirect('/login') # redirect to the login page

# prior pieces route
@app.route('/prior-pieces')
# @login_required
def prior_pieces():
    # find the user in the users database
    user = User.query.filter_by(username=session['user_id']).first()
    
    if not user:
        return "User not found."
    
    # get all stories using the relationship defined between the databases
    stories = user.stories
    
    # handle the case where users have no stories
    if not stories:
        stories = []
    
    # return a page with the user's prior stories
    return render_template('prior-pieces.html', writing=stories)

# user's account page
@app.route('/my-account')
@login_required # add login required decorator
def my_account(): 
    # get the user
    user = User.query.get(session['user_id'])
    
    # if there isn't a user, make the user login
    if not user:
        return redirect(url_for('login'))
    
    # otherwise, return the my account page
    return render_template('my-account.html', username=user.username, total_words=user.total_word_count, points=user.points, streak=len(user.stories))

@app.route('/save-writing', methods=['GET', 'POST'])
@login_required
def save_writing():
    print("Starting save_writing function")  # Debug point 1
    try:
        # Handle GET requests
        if request.method == "GET":
            print("Returning GET redirect")  # Debug point 2
            return redirect('/home')
        
        # Handle POST request
        if 'story' not in request.form or 'title' not in request.form:
            print("Missing form data")  # Debug point 3
            return "Missing required form data", 400
            
        written_raw = request.form['story']
        title = request.form['title']
        
        if not all([written_raw, title]):
            print("Invalid request - empty data")  # Debug point 4
            return "Invalid request", 400
        
        print(f"Processing story: {title[:20]}...")  # Debug point 5
        # Process the story
        story_words = written_raw.split(" ")
        word_count = len(story_words)
        
        prompts_used = sum(1 for prompt in prps.values() if prompt and prompt.lower() in map(str.lower, story_words))
        points_earned = calculate_points(prompts_used, written_raw)
        
        print("Creating new story in database")  # Debug point 6
        # Database operations
        new_story = Story(
            title=title,
            story_content=written_raw,
            prompt=str(prps),
            word_count=word_count,
            author_id=session['user_id']
        )
        
        db.session.add(new_story)
        
        user = User.query.get(session['user_id'])
        user.total_word_count += word_count
        user.points += points_earned
        
        print("Committing to database")  # Debug point 7
        db.session.commit()
        
        print("Rendering template")  # Debug point 8
        # Ensure we return a response
        return render_template(
            "congrats.html",
            title=title,
            story_len=word_count,
            words=word_count,
            points=points_earned,
            prompts=prps
        )
    
    except Exception as e:
        print(f"Exception occurred: {str(e)}")  # Debug point 9
        if 'db' in globals() and hasattr(db, 'session'):
            db.session.rollback()
        return f"An error occurred: {str(e)}", 500

    print("Reached end of function")  # Debug point 10
    return "An unexpected error occurred", 500

# read a story page
@app.route("/read-story/<story_title>")
# @login_required
def read_story(story_title):
    # get the story from the database
    story = Story.query.filter_by(title=story_title).first()
    
    # if the story doesn't exist, return an error
    if not story:
        print("[ Error ] Story not found.")
        return redirect(url_for("prior_pieces"))

    # return the page for reading the story
    return render_template("read-story.html", story=story)

# mainloop
if __name__ == "__main__":
    app.run(port=8080, debug=True)