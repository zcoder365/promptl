# general imports
from flask import *
import os
from functools import wraps # preserves function metadata
import logging

# import other files
from prompts import *
from accounts import *
from model import *
import data.data as d

# create databases
d.create_databases()

# create the flask app
app = Flask(__name__)
app.secret_key = 'key'

# page when the user comes to promptl (change this so there's a landing page?)
@app.route('/')
def index():
    return render_template('signup.html')

# added to check if the user is logged in
def login_required(f):
    @wraps(f)
    
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for('login'))
    
        return f(*args, **kwargs)
    
    return decorated_function

# home page route
@app.route('/home')
@login_required # call the function decorator
def home():
    # generate the prompts
    p = gen_all_prompts()
    
    # allocate each prompt to a variable
    name = p['name']
    job = p['job']
    place = p['place']
    object = p['object']
    bonus = p['bonus']

	# # update the prompts
    # prompts = {'name': name, 'job': job, 'place': place, 'object': object, 'bonus': bonus}

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
        username = request.form.get("username")
        password = request.form.get("password")
        parent_email = request.form.get("parent-email")
        
        # check if all required fields are filled
        if not username or not password or not parent_email:
            flash("Please fill in all fields.")
            return render_template("signup.html")
        
        # check if the user already exists
        if d.find_user(username):
            flash("Username already exists.")
            return render_template("signup.html")
        
        # add user and create session
        add_user(username, password, parent_email)
        session['username'] = username
        
        # redirect the user to the home/writing page
        return redirect(url_for("home"))
    
    # if GET request, just show signup page
    return render_template("signup.html")

# login route
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        # get username and password from the form
        username = request.form.get("username")
        password = request.form.get("password")
        
        # check if username or password is empty
        if not username or not password:
            flash("Please provide boht username and password.")
            return render_template("login.html")
        
        # use the accounts module to check login
        logged_in = login_check(username, password)
        
        if logged_in:
            # set the session
            session['username'] = username
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password.")
            return render_template("login.html")
    
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
def prior_pieces():
    # find the user's stories
    stories = d.get_user_stories(session['username'])
    
    # handle the case where users have no stories
    if not stories:
        stories = []
    
    # return a page with the user's prior stories
    return render_template('prior-pieces.html', writing=stories)

# user's account page
@app.route('/my-account')
def my_account():
    # get the user's username from the session
    username = session['username']
    
    # find the user in the database
    user = d.find_user(username)
    
    # get user's info
    num_stories = len(d.get_user_stories(username)) # get user's streak/stories written
    total_words = d.get_total_word_count(username) # get user's total word count
    points = d.get_user_points(username) # get user's points
    parent_email = d.get_parent_email(username) # get parent email
    
    # return a page that shows the user's information
    return render_template('my-account.html', username=username, total_words=total_words, parent_email=parent_email, points=points, streak=num_stories)

# FIX - save the user's writing
@app.route('/save-writing', methods=['GET', 'POST'])
@login_required
def save_writing():
    # Handle POST request for saving the writing
    if request.method == "POST":
        # Get the story content and title from the form
        written = request.form.get('story')
        title = request.form.get('title')
        
        # Get the prompts from the form
        prompts = {
            'name': request.form.get('name'),
            'job': request.form.get('job'),
            'object': request.form.get('object'),
            'place': request.form.get('place'),
            'bonus': request.form.get('bonus')
        }
        
        # Process the story
        story = written.split()  # Split the story into words
        word_count = len(story)
        
        # Calculate points earned for the story
        points_earned = process_story_points(story, prompts, word_count)
        
        # Get current user stats
        username = session.get('username')
        if not username:
            flash("Session expired. Please log in again.")
            return redirect(url_for("login"))
        
        # Save story and update user stats
        save_story_to_db(username, title, written, word_count, prompts)
        
        # Update user streak
        streak = int(d.get_user_streak(username))
        d.update_user_streak(username, streak + 1)
        
        # Update user points
        current_points = d.get_user_points(username)
        d.update_user_points(username, current_points + points_earned)
        
        # get the compliment
        compliment = gen_compliment() 
        
        # Render success page
        return render_template("congrats.html", title=title, story=written, words=word_count, compliment=compliment, points=points_earned)
    
    # handle GET request
    return redirect(url_for('home'))

# edit user's account page
@app.route("/my-account/edit")
def edit_info():
    # get the username of the current user
    username = session['username']
    
    # find the user in the database
    user = d.find_user(username)
    
    # return the template for editing user info for the current user
    return render_template("edit-info.html", user=user)

# change parent email page
@app.route('/change-email/<userID>', methods=['POST', 'GET'])
@login_required # add login check
def save_info(userID):
    # get the user's parent's email 
    parent_email = request.form['changed']
    
    # only update if a parent email is provided
    if parent_email:
        d.change_parent_email(parent_email, session['username'])
        flash("Email updated successfully!")
    else:
        flash("Please provide an email address.")

	# return to the user's account page
    return redirect(url_for('my_account'))

# read a story page
@app.route("/read-story/<story_title>")
def read_story(story_title):
    # get the story from the story database
    story = d.find_story(story_title)
    
    if not story:
        flash("Story not found.")
        return redirect(url_for("prior_pieces"))
    
    # check if the logged-in user is the author
    if story[0] != session["username"]: # assuming story[0] contains author username
        flash("You don't have permission to view the story.")
        return redirect(url_for('prior_pieces'))
    
	# return the page for reading the story
    return render_template("read-story.html", story=story)

# edit a story, based on the story's ID
@app.route("/edit-story/<story_title>")
def edit_story(story_title):
    # get the story from the db
    story = d.find_story(story_title)
    
    if not story:
        flash("Story not found.")
        return redirect(url_for("prior_pieces"))
    
    # check if the logged-in user is the author
    if story[0] != session['username']:  # assuming story[0] contains author username
        flash('You do not have permission to edit this story.')
        return redirect(url_for('prior_pieces'))
    
    # return the page for editing a story
    return render_template("edit-story.html", story=story)

app.run(port="8080", debug=True)