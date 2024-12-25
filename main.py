# general imports
from flask import *
import os
from functools import wraps # preserves function metadata
import logging

# import other files
from helpers.accounts import *
from helpers.model import *
from helpers.prompts import *
from data.data import *

# create databases
d.create_databases()

# create the flask app
app = Flask(__name__)
app.secret_key = 'key' # move to an environment variable?

# page when the user comes to promptl
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
            print("Please provide both username and password.")
            return render_template("login.html")
        
        # use the accounts module to check login
        logged_in = login_check(username, password)
        
        if logged_in:
            # set the session
            session['username'] = username
            return redirect(url_for("home"))
        else:
            print("Invalid username or password.")
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
@login_required
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
    # get the user's username
    username = session['username']
    
    # find the user in the database
    user = d.find_user(username)
    
    # get user's info
    num_stories = len(d.get_user_stories(username)) # num stories
    total_words = d.get_total_word_count(username) # total word count
    points = d.get_user_points(username) # points
    parent_email = d.get_parent_email(username) # parent email
    
    # return a page that shows the user's information
    return render_template('my-account.html', username=username, total_words=total_words, parent_email=parent_email, points=points, streak=num_stories)

# save the user's writing
@app.route('/save-writing', methods=['GET', 'POST'])
@login_required
def save_writing():
    # handle POST request for saving the writing
    if request.method == "POST":
        # get the story content and title from the form
        written_raw = request.form.get('story')
        title = request.form.get('title')
        username = session.get('username')
        
        # validate required data
        if not all([written_raw, title, username]):
            flash("Missing required information.")
            return redirect(url_for("home"))
        
        # get the prompts from the form
        prompts = {
            'name': request.form.get('name'),
            'job': request.form.get('job'),
            'object': request.form.get('object'),
            'place': request.form.get('place'),
            'bonus': request.form.get('bonus')
        }
        
        # process the story
        story = written_raw.split(" ")
        word_count = len(story)
        points_earned = process_story_points(story, prompts, word_count)
            
        # calcualate how many prompts were used
        words_used = sum(1 for prompt in prompts.values() if prompt and prompt.lower() in map(str.lower, story))
            
        # save story and update stats
        save_story_to_db(username, title, written_raw, word_count, prompts)
            
        # update user streak and points
        with d.get_db_connection(d.USER_DATA_FILE) as conn:
            cur = conn.cursor()
            cur.execute('BEGIN TRANSACTION')
                
            try:
                # update streak
                cur.execute("UPDATE users SET streak = streak + 1 WHERE username = ?", (username,))
                
                # update points
                cur.execute("UPDATE users SET points = points + ? WHERE username = ?", (points_earned, username))
                
                cur.execute('COMMIT')
            except:
                cur.execute('ROLLBACK')
                raise
    
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
    user = d.find_user(username)
    
    # return the template for editing user info for the current user
    return render_template("edit-info.html", user=user)

# change parent email page
@app.route('/change-email', methods=['POST', 'GET'])
@login_required
def save_info():
    if request.method == 'POST':
        # get the user's parent's email 
        parent_email = request.form.get('changed')
        
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
@login_required
def read_story(story_title):
    # get the story from the story database
    story = d.find_story(story_title)
    
    if not story:
        flash("Story not found.")
        return redirect(url_for("prior_pieces"))
    
    # check if the logged-in user is the author
    if story[0] != session["username"]:
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

# run the app
if __name__ == '__main__':
    app.run(port=8080, debug=True) # port is integer, not string