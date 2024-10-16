# general imports
from flask import *

# import other files
import prompts, accounts, model
import data.data as d

# create databases
d.create_databases()

# create an instance of a flask app
app = Flask(__name__)

# create variable for prompts
prompts = {}

# login signup page when the user comes to promptl (change this so there's a landing page?)
@app.route('/')
def index():
    return render_template('signup.html')

# home page route
@app.route('/home')
def home():
    # generate the prompts
    name = prompts.gen_name()
    job = prompts.gen_job()
    place = prompts.gen_place()
    object = prompts.gen_object()
    bonus = prompts.gen_bonus()

	# update the prompts
    prompts = {'name': name, 'job': job, 'place': place, 'object': object, 'bonus': bonus}

	# return the main page for writing with the prompts
    return render_template('index.html', prompts=prompts)

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
        
    logged_in = accounts.login_check(username, password)
    
    if logged_in:
        return redirect(url_for("home"))

# logout route
@app.route('/logout')
def logout():
    # remove the session
    session.clear()
    
    # return the user to the login/signup page
    return redirect(url_for('index'))

# prior pieces route - UPDATE
@app.route('/prior-pieces')
def prior_pieces():
    # find the user's stories
    # stories = writing.find({'username': session['username']})
    stories = d.get_user_stories(session['username'])
    
    # return a page with the user's prior stories
    return render_template('prior-pieces.html', writing=stories)

# user's account page - UPDATE
@app.route('/my-account')
def my_account():
    # get the user's username from the session
    username = session['username']

	# set a variable to keep track of the number of words the user wrote
    total_words = 0
    
    # find the user in the database
    # user = users.find_one({'username': username})
    user = d.find_user(username)
    
    # find the stories they wrote
    # stories = writing.find({'username': username})
    stories = d.get_user_stories(username)

	# for each story in the database...
    for story in stories:
        # get the user's total number of words they wrote
        # word_count = story['word_count']
        word_count = d.get_total_word_count(username)
        
        # increase the total_words variable by the word count of each story
        total_words += word_count
        
    # return a page that shows the user's information
    return render_template('my-account.html', users=user, total_words=total_words)

# save writing route - UPDATE
@app.route('/save-writing', methods=['GET', 'POST'])
def save_writing():
    if request.method == "POST":
        words_used = 0
        points = 0
        
        # get the story content, title
        written = request.form['story']
        title = request.form['title']
        
        # get the user's streak, increase it by one, and update it
        streak = int(d.get_user_streak(session['username']))
        new_streak = streak + 1
        
        # Update the selected user and assign new values
        d.update_user_streak(session['username'], new_streak)
        
        # create a list for the story
        story = written.split(' ')

        # get story info, word count, and points earned
        story_info = model.get_story_length_and_points(story)
        word_count = story_info['story_length']
        points_earned = story_info['points']
        
        title = request.form['title']
        
        if word_count >= 100:
            points_earned += 25
            
            # writing.insert_one({'title': title, 'story': written, 'username': session['username'], 'word_count': word_count, "prompts": prompts, "points": points})
            
            story_data = [(session['username'], title, story, word_count, prompts)]
            
            d.add_story_data(story_data)
            
            # story = writing.find_one({'title': title})
        
        # generate a random compliment for the user since they completed their story
        compliment = prompts.gen_compliment()
        
        # find the user and get their points
        user = d.find_user(session['username'])
        user_points = d.get_user_points(session['username'])
        
        # update the user's points
        new_points = points + user_points
        
        d.update_user_points(session['username'], new_points)
        
        # STOP FIXING HERE
        
    # return the congrats page
    return render_template("congrats.html", title=title, story=story, words=word_count, written=word_count, compliment=compliment, points=points)

# edit user's account page
@app.route("/my-account/edit")
def edit_info():
    # get the username of the current user
    username = session['username']
    
    # find the user in the database
    user = d.find_user(username)
    
    # return the template for editing user info for the current user
    return render_template("edit-info.html", user=user)

# change parent email page - UPDATE
@app.route('/change-email/<userID>', methods=['POST', 'GET'])
def save_info(userID):
    # get the user's parent's email 
    parent_email = request.form['changed']
    
    d.change_parent_email(parent_email, session['username'])

	# return to the user's account page
    return redirect(url_for('my_account'))

# read a story page - UPDATE
@app.route("/read-story/<story_title>")
def read_story(story_title):
    # get the story from the story database
    story = d.find_story(story_title)
    
	# return the page for reading the story
    return render_template("read-story.html", story=story)

# edit a story, based on the story's ID - UPDATE
@app.route("/edit-story/<story_title>")
def edit_story(story_title):
    # get the story from the db
    story = d.find_story(story_title)
    
    # return the page for editing a story
    return render_template("edit-story.html", story=story)

# REVIEW - DO I NEED IN THE FUTURE?
# # update story route - UPDATE
# @app.route('/update-story/<story_title>')
# def update_story(story_title):
#     if request.method == "POST":
#         # get the story from the database
#         # writing = client["promptl_data"]['writing']
#         story = d.find_story(story_title)
        
#         # get the updated story from the web page
#         updated_story = request.form['updated_story']
        
#         # get the id of the story using ObjectID from PyMongo
#         myquery = {"_id": ObjectId(storyID)}
        
#         # get the new values from the form
#         newvalues = {"$set": {'story': story}}
        
#         # update the story with the story (gotten by ID) with the new values
#         writing.update_one(myquery, newvalues)
        
#     # go back to the prior pieces page
#     return redirect(url_for('prior_pieces'))

app.run(debug=True)