# general imports
import os
from flask import Flask, request, session, redirect, url_for, render_template
from functools import wraps # preserves function metadata
from flask_sqlalchemy import SQLAlchemy

# import other files
from utils.accounts import *
from utils.prompts import *
from utils.model import *

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

# global variables
prps = None

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
        # get username, password, and parent email
        username = request.form["username"]
        password = request.form["password"]
        parent_email = request.form["parent_email"]
        
        # # check if all required fields are filled
        # if not username or not password or not parent_email:
        #     # flash("Please fill in all fields.")
        #     print("[ Error ] Please fill in all fields.")
        #     return render_template("signup.html")
        
        # # check if the user already exists
        # if db.find_user(username):
        #     # flash("Username already exists.")
        #     print("[ Error ] Username already exists.")
        #     return render_template("signup.html")
        
        # # add user and create session
        # add_user(username, password, parent_email)
        # session['username'] = username
        
        # create a new user with SQLAlchemy
        new_user = User(username, password, parent_email)
        
        session.add(new_user)
        session.commit
        
        # redirect the user to the home/writing page
        return redirect(url_for("home"))
    
    # if GET request, just show signup page
    return render_template("signup.html")

# login route
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        # get username and password from the form
        username = request.form["username"]
        password = request.form["password"]
        
        # simplified login check
        if db.verify_login(username, password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            print("[ Error ] Invalid credentials")
            return redirect(url_for('login'))
    
    # if GET request, just show the login page
    return render_template("login.html")

# logout route
@app.route('/logout')
def logout():
    # remove the session
    session.clear()
    
    # return the user to the login/signup page
    return redirect(url_for('index'))

# prior pieces route
@app.route('/prior-pieces')
# @login_required
def prior_pieces():
    user = session.query(User).get(session['user_id'])
    stories = user.stories # use SQLAlchemy relation to get the stories
    
    # handle the case where users have no stories
    if not stories:
        stories = []
    
    # return a page with the user's prior stories
    return render_template('prior-pieces.html', writing=stories)

# user's account page
@app.route('/my-account')
def my_account(): 
    # get the user's username
    username = session['username']
    
    # find the user in the database
    db.find_user(username)
    # get user's info
    num_stories = len(db.get_user_stories(username)) # num stories
    total_words = db.get_total_word_count(username) # total word count
    points = db.get_user_points(username) # points
    parent_email = db.get_parent_email(username) # parent email
    
    # return a page that shows the user's information
    return render_template('my-account.html', username=username, total_words=total_words, parent_email=parent_email, points=points, streak=num_stories)

# save the user's writing
@app.route('/save-writing', methods=['GET', 'POST'])
@login_required # apply the decorator so the route is protected
def save_writing():
    # handle POST request for saving the writing
    if request.method == "POST":
        # get the story content and title from the form
        written_raw = request.form['story']
        title = request.form['title']
        username = session['username']
        
        # # validate required data
        # if not all([written_raw, title, username]):
        #     # flash("Missing required information.")
        #     print("[ Error ] Missing information.")
        #     return redirect(url_for("home"))
        
        # get the prompts from the form
        prompts = {
            'name': prps['name'],
            'job': prps['job'],
            'object': prps['object'],
            'place': prps['place'],
            'bonus': prps['bonus']
        }
        
        # process the story
        story = written_raw.split(" ")
        word_count = len(story)
        points_earned = calculate_points(story, prompts, word_count)
            
        # calculate how many prompts were used
        words_used = sum(1 for prompt in prompts.values() if prompt and prompt.lower() in map(str.lower, story))
            
        # create a new story with SQLAlchemy
        new_story = Story(
            prompt=str(prompts),
            word_count=word_count,
            author_id=session['user_id']
        )
        
        # add the story to the database
        session.add(new_story)
        
        # update user's stotal word count
        user = session.query(User).get(session['user_id'])
        user.total_word_count += word_count
        user.points += points_earned
        
        # commit changes
        session.commit()
    
        # get the compliment
        compliment = gen_compliment() 
        
        # render success page
        return render_template(
            "congrats.html", 
            title=title, 
            story_len=word_count, 
            words=words_used,
            points=points_earned, 
            compliment=compliment, 
            prompts=prompts
        )
    
    # handle GET request
    return redirect(url_for('home'))

# edit user's account page
@app.route("/my-account/edit")
def edit_info():
    # get the username of the current user and their info from the database
    username = session['username']
    user = db.find_user(username)
    
    # return the template for editing user info for the current user
    return render_template("edit-info.html", user=user)

# change parent email page
@app.route('/change-email', methods=['POST', 'GET'])
# @login_required
def save_info():
    if request.method == 'POST':
        # get the user's parent's email 
        parent_email = request.form['changed']
        
        # only update if a parent email is provided
        if parent_email:
            db.change_parent_email(parent_email, session['username'])
            # flash("Email updated successfully!")
            print("[ Success ] Email updated successfully.")
        
        else:
            # flash("Please provide an email address.")
            print("[ Error ] Please enter a valid email address.")

    # return to the user's account page
    return redirect(url_for('my_account'))

# read a story page
@app.route("/read-story/<story_title>")
# @login_required
def read_story(story_title):
    # get the story from the story database
    story = db.find_story(story_title)
    
    if not story:
        # flash("Story not found.")
        print("[ Error ] Story not found.")
        return redirect(url_for("prior_pieces"))
    
    # check if the logged-in user is the author
    if story[0] != session["username"]:
        # flash("You don't have permission to view the story.")
        print("[ Error ] You don't have permission to view the story.")
        return redirect(url_for('prior_pieces'))
    
    # return the page for reading the story
    return render_template("read-story.html", story=story)

# edit a story, based on the story's ID
@app.route("/edit-story/<story_title>")
def edit_story(story_title):
    # get the story from the db
    story = db.find_story(story_title)
    
    if not story:
        # flash("Story not found.")
        print("[ Error ] Story not found.")
        return redirect(url_for("prior_pieces"))
    
    # check if the logged-in user is the author
    if story[0] != session['username']:  # assuming story[0] contains author username
        # flash('You do not have permission to edit this story.')
        print("[ Error ] You don't have permission to edit this story.")
        return redirect(url_for('prior_pieces'))
    
    # return the page for editing a story
    return render_template("edit-story.html", story=story)

# run the app
if __name__ == '__main__':
    app.run(port=8080, debug=True)