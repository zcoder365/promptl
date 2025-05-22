# add allowed hosts for the website
ALLOWED_HOSTS = ['promptl.com', 'www.promptl.com']

# import necessary libraries
from functools import wraps
from flask import Flask, request, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime

# import project files
from utils.prompts import *
from utils.model import *

# create the flask app and add configurations
app = Flask(__name__)
app.config['SECRET_KEY'] = "key"

# generate the prompts for the main page
prompts = gen_all_prompts()

# landing route
@app.route('/')
def index():
    return render_template('signup.html')

# home page route
@app.route('/home')
def home():
    # regenerate the prompts if the page is reloaded
    prompts = gen_all_prompts()
        
    # allocate each prompt to a variable
    name = prompts['name']
    job = prompts['job']
    place = prompts['location']
    object = prompts['object']
    bonus = prompts['bonus']

    # return the main page for writing with the prompts
    return render_template('index.html', name=name, job=job, object=object, place=place, bonus=bonus)

# generate a new prompt by reloading home page
@app.route('/new-prompt')
def new_prompt():
    # reload the page to get a new 5 prompts
    return redirect(url_for("home"))

# about page route
@app.route('/about')
def about_page():
    # return the page about the game
    return render_template('about.html')

# sign up route
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
        
        # SIGN UP LOGIC
    
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
        
        # LOGIN LOGIC
    
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
        stories = ""
        
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
        user = ""
        
        # if the user doesn't exist/isn't in the session, redirect user to login page
        if not user:
            return redirect(url_for('login'))
        
        # get story count for streak
        story_count = ""
        
        return render_template('my-account.html', username=user['username'], total_words=user['total_word_count'], points=user['points'], streak=story_count)
    
    except Exception as e:
        print(f"Error accessing account: {e}")
        return redirect(url_for('login'))

# save the user's writing
@app.route('/save-writing', methods=['GET', 'POST'])
def save_writing():
    if request.method == "POST":
        try:
            written_raw = request.form.get('story')
            title = request.form.get('title')
            
            # Validate input
            is_valid = validate_writing_input(written_raw, title)
            if not is_valid:
                if is_valid == True:
                    error_message = ""
                elif is_valid == False:
                    error_message = "Please fill in all fields."
                return render_template("index.html", message=error_message)
            
            # Get user ID
            try:
                user_id = ObjectId(session.get('user_id'))
            except:
                return render_template("index.html", message="User session expired. Please log in again.")
            
            # Process story metrics
            metrics = process_story_metrics(written_raw, prompts)
            
            # Create and save story
            story_doc = create_story_document(title, written_raw, prompts, metrics, user_id)
            
            # SAVE THE STORY TO THE DATABASE - ADD LOGIC
            
            # if not success:
            #     return render_template("index.html", message=f"An error occurred: {result}")
            
            return render_template("congrats.html", title=title, story_len=metrics['word_count'], points=metrics['points'], words=metrics['num_used_prompts'])
                                
        except Exception as e:
            print(f"Error saving writing: {e}")
            return render_template("index.html", message=f"An error occurred: {str(e)}")
    
    return redirect(url_for("home"))

# read a story page
@app.route("/read-story/<story_title>")
def read_story(story_title):
    try:
        # find a specific story in the user's database
        story = ""
        
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
    app.run(host="0.0.0.0", port=8080, debug=True)