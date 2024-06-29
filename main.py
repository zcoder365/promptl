import pymongo
from flask import *
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os
import bcrypt
import model

app = Flask(__name__)

# load dotenv file and get URI
load_dotenv()
URI = os.getenv("URI")

# set the uri for MongoDB to URI
app.config['MONGO_URI'] = URI

# get the database from mongodb
app.config['MONGO_DBNAME'] = 'promptl_data'

# set up the client
client = pymongo.MongoClient(URI)

# get the general data
data = client['promptl_data']

# set some global variables
global users
global writing
global title
global prompts

# get the users specifically
users = data['users']

# get the writing specifically
writing = data['writing']

# login signup page when the user comes to promptl (change this so there's a landing page?)
@app.route('/')
def index():
    return render_template('create_account.html')

# home page route
@app.route('/home')
def home():
    # generate the prompts
    name = model.gen_name()
    job = model.gen_job()
    place = model.gen_place()
    object = model.gen_object()
    bonus = model.gen_bonus()

	# update the prompts
    prompts = {
        'name': name,
        'job': job,
        'place': place,
        'object': object,
        'bonus': bonus
    }

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

# check signup for the user
@app.route('/signup/check', methods=['GET', 'POST'])
def signup_check():
    if request.method == 'POST':
        # users = mongo.db.users
        # users = data['users']
        
        # determine if the user exists
        existing_user = users.find_one({'username': request.form['username']})
        
		# get the username, password, and parent email from the form
        un = request.form['username']
        pw = request.form['password']
        parent_email = request.form['parent_email']
        
        if not existing_user:
            # Create a hash of the user's password
            hashpass = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
            
            users.insert_one({ 'username': un, 'password': str(hashpass, 'utf-8'), 'parent_email': parent_email, 'points': 0, 'streak': 0, "prizes": 0, "average_words": 0})
            
            session['username'] = request.form['username']
            
            return redirect(url_for('home'))
        
        elif existing_user:
            return 'That username already exists! Try logging in.'
        
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
    
    if not username or not password:
        return 'Please provide both username and password.'
    
    # determine if the user exists
    login_user = users.find_one({"username": username})
    
    if login_user:
        if bcrypt.checkpw(password.encode('utf-8'), login_user['password'].encode('utf-8')):
            session['username'] = username
            return redirect(url_for("home"))
    
    return 'Invalid username-password combination. Please try again.'

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
    stories = writing.find({'username': session['username']})
    
    # return a page with the user's prior stories
    return render_template('prior-pieces.html', writing=stories)

# user's accoutn page
@app.route('/my-account')
def my_account():
    # get the user's username from the session
    username = session['username']

	# set a variable to keep track of the number of words the user wrote
    total_words = 0
    
    # find the user in the database
    user = users.find_one({'username': username})
    
    # find the stories they wrote
    stories = writing.find({'username': username})

	# for each story in the database...
    for story in stories:
        # get the user's total number of words they wrote
        word_count = story['word_count']
        
        # increase the total_words variable by the word count of each story
        total_words += word_count
        
    # return a page that shows the user's information
    return render_template('my-account.html', users=user, total_words=total_words)

# save writing route
@app.route('/save-writing', methods=['GET', 'POST'])
def save_writing():
    if request.method == "POST":
        words_used = 0
        points = 0
        
        # get the story content
        written = request.form['story']
        
        # get the story title
        title = request.form['title']
        
        # find the user in the database
        user = users.find_one({'username': session['username']})
        
        # get the user's ID
        userID = user['_id']
        
        # get the user's streak and increase it by one
        streak = int(user['streak'])
        new_streak = streak + 1
        
        # Find the user to edit using userID
        myquery = {"_id": PyMongo.ObjectId(userID)} 
        
        # Create new values to update the user
        new_streak = {"$set": {'streak': new_streak}}
        
        # Update the selected user and assign new values
        users.update_one(myquery, new_streak)
        
        # insert the prompts to the user's story
        writing.insert_one({"prompts": prompts})
        prompt_id = writing['_id']
        
        # create a list for the story
        story = written.split(' ')
        
        # get it's length/number of words
        words_written = len(story)
        
        if words_written >= 70:
            if prompts['name'] in written.upper():
                points += 10
                words_used += 1
                
            elif prompts['name'] not in written.upper():
                pass
            
            if prompts['job'] in written.upper():
                points += 10
                
                words_used += 1

            elif prompts['job'] not in written.upper():
                pass
            
            if prompts['object'] in written.upper():
                points += 10
                words_used += 1
                
            elif prompts['object'] not in written.upper():
                pass
            
            if prompts['place'] in written.upper():
                points += 10
                words_used += 1
                
            elif prompts['place'] not in written.upper():
                pass
            
            if prompts['bonus'] in written.upper():
                points += 20
                words_used += 1
                
            elif prompts['bonus'] not in written.upper():
                pass
            
        story = written.upper()
        story = story.split()
        story_word_count = int(len(story))
        
        title = request.form['title'] # referenced before assignment; but this is the assignment...
        
        if story_word_count >= 100:
            points += 25
            
            writing.insert_one({'title': title, 'story': written, 'username': session['username'], 'word_count': story_word_count, "prompts": prompts, "points": points})
            
            story = writing.find_one({'title': title})
            
    	# get the number of words the user used
        words = words_used
        
        # generate a random compliment for the user since they completed their story
        compliment = model.gen_compliment()
        
        # find the user and get their points
        user = users.find_one({"_id": PyMongo.ObjectId(userID)})
        user_points = int(user['points'])
        
        # update the user's points
        add_points = points + user_points
        
		# update the user's info in the database
        myquery = {"_id": PyMongo.ObjectId(userID)}
        new_points = {"$set": {'points': add_points}}
        users.update_one(myquery, new_points)
        
    # return the congrats page
    return render_template("congrats.html", title=title, story=story, words=words, written=story_word_count, compliment=compliment, points=points)

# edit user's account page
@app.route("/my-account/edit")
def edit_info():
    # get the username of the current user
    username = session['username']
    
    # find the user in the databse
    user = users.find_one({'username': username})
    
    # return the template for editing user info for the current user
    return render_template("edit-info.html", user=user)

# change parent email page
@app.route('/change-email/<userID>', methods=['POST', 'GET'])
def save_info(userID):
    # get the user's parent's email 
    parent_email = request.form['changed']
    
    # Find the user to edit using userID
    myquery = {"_id": PyMongo.ObjectId(userID)}
    
    # Create new values to update the user
    newvalues = {"$set": {'parent_email': parent_email}}
    
    # Update the selected user and assign new values
    users.update_one(myquery, newvalues)
    
    # Find the newly edited user
    users = users.find_one({'_id': PyMongo.ObjectId(userID)})

	# return to the user's account page
    return redirect(url_for('my_account'))

# read a story page
@app.route("/read-story/<storyID>")
def read_story(storyID):
    # get the database for the stories the user wrote
    writing = client['promptl_data']['writing']
    
    # get the story's ID
    story = writing.find_one({"_id": PyMongo.ObjectId(storyID)})
    
	# return the page for reading the story
    return render_template("read-story.html", story=story)

# edit a story, based on the story's ID
@app.route("/edit-story/<storyID>")
def edit_story(storyID):
    # get the writing databsae
    writing = client['promptl_data']['writing']
    
    # find the story and get it's ID
    story = writing.find_one({"_id": PyMongo.ObjectId(storyID)})
    
    # return the page for editing a story
    return render_template("edit-story.html", story=story)

# update story route
@app.route('/update-story/<storyID>')
def update_story(storyID):
    if request.method == "POST":
        # get the story from the database
        writing = client["promptl_data"]['writing']
        
        # get the updated story from the web page
        story = request.form['updated_story']
        
        # get the id of the story using ObjectID from PyMongo
        myquery = {"_id": PyMongo.ObjectId(storyID)}
        
        # get the new values from the form
        newvalues = {"$set": {'story': story}}
        
        # update the story with the story (gotten by ID) with the new values
        writing.update_one(myquery, newvalues)
        
    # go back to the prior pieces page
    return redirect(url_for('prior_pieces'))

app.run(debug=True)