# add allowed hosts
ALLOWED_HOSTS = ['promptl.com', 'www.promptl.com']

# general imports
import os
from dotenv import load_dotenv
from functools import wraps
from flask import Flask, request, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo import MongoClient, ServerApi
from bson import ObjectId
from datetime import datetime

# import other files
from utils.prompts import *
from utils.model import *

# create the flask app and add configurations
app = Flask(__name__)
app.config['SECRET_KEY'] = "key"

# get info from dotenv file
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI") # get db uri

# mongodb connection with proper error handling
try:
    client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
    # send a ping for confirmation
    client.admin.command('ping')
    print("Successfully created to MongoDB")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    raise

db = client['promptl_db'] # change to db name
users_collection = db['users'] # get users collection connection
stories_collection = db['stories'] # get stories collection connection

# GLOBAL VARIABLES
prps = gen_all_prompts() # generate the prompts

# login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
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
        # get info from form
        username = request.form["username"]
        password = request.form["password"]
        
        # validate input
        if not username or not password:
            return render_template("signup.html", message="Please fill in all fields.")
        
        if len(password) < 6:
            return render_template("signup.html", message="Password must be at least 6 characters.")
        
        if len(username) < 3:
            return render_template("signup.html", message="Username must be at least 3 characters.")
        
        # check if user exists using MongoDB
        existing_user = users_collection.find_one({"username": username})
        if existing_user:
            return render_template("signup.html", message="Username already exists.")
        
        try:
            # create new user document
            new_user = {
                "username": username,
                "password": generate_password_hash(password),
                "points": 0,
                "total_word_count": 0,
                "created_at": datetime.utcnow()
            }
            
            # insert into MongoDB
            result = users_collection.insert_one(new_user)
            
            return redirect(url_for("login"))
        
        except Exception as e:
            print(f"Error during signup: {e}")
            return render_template("signup.html", message="An error occurred during signup.")
    
    return render_template("signup.html")

# login route
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        # get info from form
        username = request.form["username"]
        password = request.form["password"]
        
        # validate input
        if not username or not password:
            return render_template("login.html", message="Please fill in all fields.")
        
        # find user in MongoDB
        user = users_collection.find_one({"username": username})
        
        # confirm passwords match
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])  # Convert ObjectId to string
            return redirect(url_for('home'))

        return render_template("login.html", message="Invalid username or password.")
    
    return render_template("login.html")

# logout route
@app.route('/logout')
def logout():
    session.clear() # clear the session
    return redirect('/login') # redirect to the login page

# prior pieces route
@app.route('/prior-pieces')
def prior_pieces():
    # get user's stories from MongoDB
    try:
        # get user id
        user_id = ObjectId(session['user_id'])
        
        # find stories based on user's id
        stories = stories_collection.find({"author_id": user_id})
        
        # convert cursor to a list
        stories_list = list(stories)
        
        return render_template('prior-pieces.html', stories=stories_list)
    
    except Exception as e:
        print(f"Error retrieving stories: {e}")
        return render_template('prior-pieces.html', stories=[])

# user's account page
@app.route('/my-account')
def my_account():
    try:
        # get the user's id and find the user
        user_id = ObjectId(session['user_id'])
        user = users_collection.find_one({"_id": user_id})
        
        # if the user doesn't exist/isn't in the session, redirect user to login page
        if not user:
            return redirect(url_for('login'))
        
        # get story count for streak
        story_count = stories_collection.count_documents({"author_id": user_id})
        
        return render_template('my-account.html', username=user['username'], total_words=user['total_word_count'], points=user['points'], streak=story_count)
    
    except Exception as e:
        print(f"Error accessing account: {e}")
        return redirect(url_for('login'))

# save the user's writing
@app.route('/save-writing', methods=['GET', 'POST'])
# @login_required
def save_writing():
    if request.method == "POST":
        try:
            # get the story content and title from the form
            written_raw = request.form['story']
            title = request.form['title']
            
            if not all([written_raw, title]):
                return "Invalid request."
            
            # get the word count
            story_words = written_raw.split()  # Changed to split() without argument to handle multiple spaces
            word_count = len(story_words)
            
            # calculate the prompts used
            prompts_used = sum(1 for prompt in prps.values() if prompt and prompt.lower() in map(str.lower, story_words))
            
            # get the points earned for writing the story
            points_earned = calculate_points(prps, written_raw)
            
            # get the user first to ensure they exist
            user = User.query.get(session['user_id'])
            if not user:
                return "User not found.", 404
            
            # create a new story with SQLAlchemy
            new_story = Story(
                title=title,
                story_content=written_raw,
                prompt=str(prps),
                word_count=word_count,
                points=points_earned, # add points to the story
                author_id=user.id  # use user.id instead of session['user_id']
            )
            
            # add story to the database
            db.session.add(new_story)
            
            # update user stats
            user.total_word_count += word_count
            user.points += points_earned
            
            # commit changes to the database
            db.session.commit()
            
            return render_template("congrats.html", title=title, story_len=word_count, words=prompts_used, points=points_earned, prompts=prps)

        except Exception as e:
            db.session.rollback()
            print(f"Error saving writing: {str(e)}") # add logging for debugging
            return render_template("index.html", message="An error occurred while saving your story.")
    
    return redirect(url_for("home"))

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
    app.run(host="0.0.0.0", port=80)
    # app.run()