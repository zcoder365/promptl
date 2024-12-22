# general imports
from flask import *
import os
from functools import wraps # preserves function metadata

# import other files
import prompts, accounts, model
import data.data as d

# create databases
d.create_databases()

# create the flask app
app = Flask(__name__)
app.secret_key = 'key'

# login signup page when the user comes to promptl (change this so there's a landing page?)
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
    p = prompts.gen_all_prompts()
    
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
@app.route("/signup")
def signup():
    return render_template("signup.html")

# check signup for the user
@app.route('/signup/check', methods=['POST'])
def signup_check():
    # get username, password, and parent email from form
    username = request.form.get("username")
    password = request.form.get("password")
    parent_email = request.form.get("parent-email")
    
    accounts.add_user(username, password, parent_email)
    
    session['username'] = username
        
    # redirect the user to the home/writing page
    return redirect(url_for("home"))

# LOGIN ROUTE
@app.route("/login")
def login():
    return render_template("login.html")

# LOGIN CHECK ROUTE
@app.route('/login/check', methods=['POST'])
def login_check():
    # get user from form and determine if they exist
    username = request.form.get("username")
    password = request.form.get("password")
    
    # if the username or password doesn't exist
    if username == "" or username == None or password == "" or password == None:
        flash('Please provide both username and password.')
    
    return redirect(url_for("home"))

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
    
    # # find the user in the database
    # user = d.find_user(username)
    # if not user:
    #     return redirect(url_for("login"))
    
    # find the stories they wrote
    stories = d.get_user_stories(username)
    
    total_words = d.get_total_word_count(username)
    
    # return a page that shows the user's information
    return render_template('my-account.html', users=user, total_words=total_words)

# save the user's writing
@app.route('/save-writing', methods=['GET', 'POST'])
@login_required
def save_writing():
    if request.method == "POST":
        # Initialize points
        points = 0
        
        # Get the story content and title
        written = request.form['story']
        title = request.form['title']
        
        # Get the prompts from the form
        prompts = {
            'name': request.form.get('name'),
            'job': request.form.get('job'),
            'object': request.form.get('object'),
            'place': request.form.get('place'),
            'bonus': request.form.get('bonus')
        }
        
        # Get the user's streak, increase it by one, and update it
        streak = int(d.get_user_streak(session['username']))
        new_streak = streak + 1
        d.update_user_streak(session['username'], new_streak)
        
        # Create a list for the story
        story = written.split(' ')
        
        # Get story info, word count, and points earned
        story_info = model.get_story_length_and_points(story, prompts)  # Added prompts parameter
        word_count = story_info['story_length']
        points_earned = story_info['points']
        
        if word_count >= 100:
            points_earned += 25
            
            # Create story data tuple with correct format
            story_data = (session['username'], title, written, word_count, str(prompts))  # Changed to tuple, converted prompts to string
            d.add_story_data(story_data)
        
        # Generate a random compliment
        compliment = prompts.gen_compliment()
        
        # Get user points and update them
        user_points = d.get_user_points(session['username'])
        new_points = points_earned + user_points  # Changed to points_earned instead of points
        d.update_user_points(session['username'], new_points)
        
        # Return the congrats page with updated values
        return render_template("congrats.html", title=title, story=written, words=word_count, written=word_count, compliment=compliment, points=points_earned)  # Changed to points_earned
    
    # If not POST method, redirect to home
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