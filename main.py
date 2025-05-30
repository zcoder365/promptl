# add allowed hosts for the website
ALLOWED_HOSTS = ['promptl.com', 'www.promptl.com']

# import necessary libraries
from functools import wraps
from flask import Flask, request, session, redirect, url_for, render_template, flash
from werkzeug.security import generate_password_hash, check_password_hash
# from bson import ObjectId
import bcrypt
# from datetime import datetime

# import project files
import utils.prompts as prompts
import utils.model as model
import utils.database as db

# create the flask app and add configurations
app = Flask(__name__)
app.config['SECRET_KEY'] = "key"

# generate the prompts for the main page
story_prompts = prompts.gen_all_prompts()

# create a login decorator to check if the user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# landing route
@app.route('/')
def index():
    return render_template('signup.html')

# home page route
@app.route('/home')
@login_required
def home():
    # regenerate the prompts if the page is reloaded
    story_prompts = prompts.gen_all_prompts()
        
    # allocate each prompt to a variable
    name = story_prompts['name']
    job = story_prompts['job']
    place = story_prompts['location']
    object = story_prompts['object']
    bonus = story_prompts['bonus']

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
        
        # prevent extremely long passwords
        if len(password) > 128:
            return render_template("signup.html", message="Password must be less than 128 characters.")
        
        if len(username) < 3:
            return render_template("signup.html", message="Username must be at least 3 characters.")
        
        # add maximum length check for username
        if len(username) > 50:
            return render_template("signup.html", message="Username must be less than 50 characters.")
        
        # check if username already exists (removed the duplicate call)
        try:
            existing_user = db.get_user(username)
            if existing_user:
                return render_template("signup.html", message="Username already exists. Please choose another.")
        except Exception as e:
            # log the error for debugging but don't expose it to user
            print(f"Database error checking user: {e}")
            return render_template("signup.html", message="An error occurred. Please try again.")
        
        # hash the password before storing
        try:
            hashed_password = generate_password_hash(password)
            print(f"Debug - Password hashed successfully for user: {username}")  # Debug line
        
        except Exception as e:
            print(f"Password hashing error: {e}")
            return render_template("signup.html", message="An error occurred. Please try again.")
        
        # attempt to create the new user
        try:
            result = db.add_user(username, hashed_password)
            
            # Check if user creation was successful
            if result is not None:
                # success - redirect to login with success message
                flash("Account created successfully! Please log in.", "success")
                return redirect(url_for('login'))
            
            else:
                # database operation failed - this is where your error is occurring
                return render_template("signup.html", message="Failed to create account. Please try again.")
                
        except Exception as e:
            # handle any unexpected errors during user creation
            print(f"Error creating user account: {e}")
            
            return render_template("signup.html", message="An error occurred while creating your account. Please try again.")
    
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
        
        # find the user in the database (if they exist)
        user = db.get_user(username)
        
        # if the user exists, check if the password is correct
        if user != None:
            # debugging
            print(f"Debug - User found: {username}")
            print(f"Debug - Password field exists: {'password' in user}")
            
            # Check if it's a bcrypt hash (starts with $2b$) or werkzeug hash
            stored_password = user['password']
            password_correct = False
            
            if stored_password.startswith('$2b$') or stored_password.startswith('$2a$'):
                # This is a bcrypt hash - need to check it with bcrypt
                import bcrypt
                password_correct = bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
                print("Debug - Checking bcrypt password")
            else:
                # This is a werkzeug hash - use check_password_hash
                try:
                    password_correct = check_password_hash(stored_password, password)
                    print("Debug - Checking werkzeug password")
                except:
                    print("Debug - Password hash format not recognized")
                    password_correct = False
            
            if password_correct:
                print("Debug - Password matched!")
                
                # store user id in session
                session['user_id'] = str(user['id'])
                session['username'] = username
                
                # redirect to home page
                return redirect(url_for('home'))
            else:
                # debugging
                print("Debug - Password did NOT match")
                
                # if the password is incorrect, return error message
                return render_template("login.html", message="Incorrect password.")
        
        else:
            # otherwise, if the user doesn't exist, return error message
            return render_template("login.html", message="Username or password is incorrect.")
    
    return render_template("login.html")

# reset password route
@app.route("/reset-password", methods=['GET', 'POST'])
def reset_password():
    if request.method == "POST":
        # get info from form
        username = request.form["username"]
        new_password = request.form["new-password"]
        
        # validate input
        if not username or not new_password:
            return render_template("reset-password.html", message="Please fill in all fields.")
        
        # find the user in the database (if they exist)
        user = db.get_user(username)
        
        # if the user exists, update the password
        if user:
            # hash the new password
            hashed_password = generate_password_hash(new_password)
            
            # update the user's password in the database
            db.update_user_password(user['id'], hashed_password)
            
            # redirect to login page
            return redirect(url_for('login'))
        
        else:
            # if the user doesn't exist, return error message
            return render_template("reset-password.html", message="Username does not exist.")
    
    # if the request method is GET, render the reset password page
    return render_template("reset-password.html")

# prior pieces route
@app.route('/prior-pieces')
@login_required
def prior_pieces():
    try:
        username = session.get('username')
        if not username:
            return redirect(url_for('login'))
        
        # Get all stories for now (we'll filter by username later when that column is added)
        stories = db.get_user_stories(username)
        
        print(f"DEBUG MAIN - Retrieved {len(stories)} stories")
        
        return render_template('prior-pieces.html', stories=stories)
    
    except Exception as e:
        print(f"DEBUG MAIN - Error retrieving stories: {e}")
        return render_template('prior-pieces.html', stories=[])

# user's account page
@app.route('/my-account')
@login_required
def my_account():
    try:
        # Get username from session
        username = session.get('username')
        if not username:
            return redirect(url_for('login'))
        
        # Get user data from database
        user = db.get_user(username)
        if not user:
            return redirect(url_for('login'))
        
        # Get user's stories to calculate streak
        stories = db.get_user_stories(username)
        story_count = len(stories)
        
        # Handle None values for user stats
        total_words = user.get('total_word_count', 0) or 0
        points = user.get('points', 0) or 0
        
        return render_template('my-account.html', 
                             username=user['username'], 
                             total_words=total_words, 
                             points=points, 
                             streak=story_count)
    
    except Exception as e:
        print(f"Error accessing account: {e}")
        return redirect(url_for('login'))

# save the user's writing
@app.route('/save-writing', methods=['GET', 'POST'])
@login_required
def save_writing():
    if request.method == "POST":
        # get info fromt the form
        written_raw = request.form.get('story')
        title = request.form.get('title')
        
        print(f"DEBUG MAIN - Received title: '{title}'")
        print(f"DEBUG MAIN - Story length: {len(written_raw) if written_raw else 0}")
        
        # Validate input data
        if not written_raw or not title:
            return render_template("index.html", message="Please provide both title and story content.")
        
        # Get username from session
        username = session.get('username')
        if not username:
            return render_template("index.html", message="User session expired. Please log in again.")
        
        print(f"DEBUG MAIN - Username: {username}")
        
        # # Get current prompts
        # if not story_prompts:
        #     story_prompts = prompts.gen_all_prompts()
        
        print(f"DEBUG MAIN - Prompts: {story_prompts}")
        
        # Calculate metrics
        metrics = model.get_story_metrics(written_raw, story_prompts)
        print(f"DEBUG MAIN - Metrics: {metrics}")
        
        # Try to save the story with the minimal function first
        story_id = db.add_story(title, written_raw, story_prompts, metrics['word_count'], metrics['points'], username)
        
        if story_id is None:
            print("DEBUG MAIN - Minimal save failed, trying full save")
            # If minimal fails, try the full version
            story_id = db.add_story(title, written_raw, story_prompts, metrics['word_count'], metrics['points'], username)
        
        if story_id:
            print(f"DEBUG MAIN - Story saved successfully with ID: {story_id}")
        
            return render_template("congrats.html", title=title, story_len=metrics['word_count'], points=metrics['points'], words=metrics['num_used_prompts'])
        
        else:
            print("DEBUG MAIN - Both save methods failed")
            return render_template("index.html", message="Failed to save story. Check console for details.")
    
    return redirect(url_for("home"))

# read a story page
@app.route("/read-story/<story_title>")
@login_required
def read_story(story_title):
    try:
        # Get username from session
        username = session.get('username')
        if not username:
            return redirect(url_for('login'))
        
        # Get user's stories and find the specific one
        stories = db.get_user_stories(username)
        story = None
        
        for s in stories:
            if s['title'] == story_title:
                story = s
                break
        
        # If story not found, redirect to prior pieces
        if not story:
            print(f"[ Error ] Story '{story_title}' not found.")
            return redirect(url_for("prior_pieces"))

        return render_template("read-story.html", story=story)
    
    except Exception as e:
        print(f"Error reading story: {e}")
        return redirect(url_for("prior_pieces"))

# logout route
@app.route('/logout')
def logout():
    session.clear() # clear the session
    return redirect('/login') # redirect to the login page

# mainloop
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)