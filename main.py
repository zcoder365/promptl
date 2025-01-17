# add allowed hosts
ALLOWED_HOSTS = ['promptl.com', 'www.promptl.com']

# general imports
import os
# from dotenv import load_dotenv
from functools import wraps
from flask import Flask, request, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
from datetime import datetime

# import other files
from utils.prompts import *
from utils.model import *

# create the flask app and add configurations
app = Flask(__name__)
app.config['SECRET_KEY'] = "key"

# get info from dotenv file
# load_dotenv()
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
def save_writing():
    if request.method == "POST":
        try:
            # Get the info from the form
            written_raw = request.form.get('story')
            title = request.form.get('title')
            prompts = request.form.get('prompts')  # Add this to get prompts from the form
            
            # Validate all required fields are present
            if not all([written_raw, title, prompts]):
                return render_template("index.html", 
                    message="Please fill in all required fields (story, title, and prompts).")
            
            # Calculate variables needed for saving the writing
            story_words = written_raw.split()
            word_count = len(story_words)
            points_earned = calculate_points(prompts, written_raw)  # Using prompts from form
            
            # Get the user's id from the session
            try:
                user_id = ObjectId(session.get('user_id'))
            except:
                return render_template("index.html", 
                    message="User session expired. Please log in again.")
            
            # Create a new story document
            new_story = {
                "title": title,
                "story_content": written_raw,
                "prompt": prompts,
                "word_count": word_count,
                "points": points_earned,
                "author_id": user_id,
                "created_at": datetime.utcnow()
            }
            
            # Insert story and verify success
            story_result = stories_collection.insert_one(new_story)
            if not story_result.inserted_id:
                raise Exception("Failed to save story to database")
            
            # Update user stats and verify success
            user_result = users_collection.update_one(
                {"_id": user_id},
                {
                    "$inc": {
                        "total_word_count": word_count,
                        "points": points_earned
                    }
                }
            )
            if user_result.modified_count == 0:
                # Rollback story insertion if user update fails
                stories_collection.delete_one({"_id": story_result.inserted_id})
                raise Exception("Failed to update user statistics")
            
            return render_template("congrats.html", 
                title=title, 
                story_len=word_count, 
                points=points_earned, 
                prompts=prompts)

        except Exception as e:
            print(f"Error saving writing: {e}")
            # Log the full error for debugging
            import traceback
            traceback.print_exc()
            return render_template("index.html", 
                message=f"An error occurred while saving your story: {str(e)}")
    
    return redirect(url_for("home"))

# read a story page
@app.route("/read-story/<story_title>")
def read_story(story_title):
    try:
        # find a specific story in the user's database
        story = stories_collection.find_one({"title": story_title})
        
        # if the story doesn't exist, return error message and the prior pieces page
        if not story:
            print("[ Error ] Story not found.")
            return redirect(url_for("prior_pieces"))

        return render_template("read-story.html", story=story)
    
    except Exception as e:
        print(f"Error reading story: {e}")
        return redirect(url_for("prior_pieces"))

# mainloop
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)