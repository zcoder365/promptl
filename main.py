# add allowed hosts for the website
ALLOWED_HOSTS = ['promptl.com', 'www.promptl.com']

# import necessary libraries
from functools import wraps
from flask import Flask, request, session, redirect, url_for, render_template, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
import bcrypt

# import project files
import utils.prompts as prompts
import utils.model as model
import utils.database as db

# create the flask app and add configurations
app = Flask(__name__)
app.config['SECRET_KEY'] = "your-more-secure-secret-key-here"  # Use a more secure key in production
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Session expires after 24 hours

# Make sessions permanent so they persist across requests
@app.before_request
def make_session_permanent():
    session.permanent = True

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
    # Generate new prompts and store them in session for later use in save_writing
    story_prompts = prompts.gen_all_prompts()
    session['current_prompts'] = story_prompts  # Store prompts in session to persist across requests
        
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
        
        # Use plain password since db.add_user() handles hashing internally
        try:
            print(f"Debug - Creating user: {username}")  # Debug line
        
        except Exception as e:
            print(f"Error preparing user data: {e}")
            return render_template("signup.html", message="An error occurred. Please try again.")
        
        # attempt to create the new user
        try:
            result = db.add_user(username, password)  # Pass plain password - db.add_user() will hash it
            
            # Check if user creation was successful
            if result is not None:
                # success - redirect to login with success message
                flash("Account created successfully! Please log in.", "success")
                return redirect(url_for('login'))
            
            else:
                # database operation failed
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
        
        # Use authenticate_user function which handles password hashing verification
        user = db.authenticate_user(username, password)
        
        if user:
            print(f"Debug - Authentication successful for user: {username}")
            
            # store user id in session
            session['user_id'] = str(user['id'])
            session['username'] = username
            
            # redirect to home page
            return redirect(url_for('home'))
        else:
            print(f"Debug - Authentication failed for user: {username}")
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
            # Use reset_user_password function which handles hashing internally
            success = db.reset_user_password(username, new_password)
            
            if success:
                flash("Password reset successfully! Please log in with your new password.", "success")
                return redirect(url_for('login'))
            else:
                return render_template("reset-password.html", message="Failed to reset password. Please try again.")
        
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
        
        # Get user-specific stories from database
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
        
        # Handle None values for user stats with proper fallback logic
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
        # get info from the form
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
        
        # Get prompts from session instead of relying on global variable
        story_prompts = session.get('current_prompts')
        if not story_prompts:
            print("DEBUG MAIN - No prompts in session, generating new ones")
            story_prompts = prompts.gen_all_prompts()  # Fallback if no prompts in session
        
        print(f"DEBUG MAIN - Prompts: {story_prompts}")
        
        # Calculate metrics using the retrieved prompts
        metrics = model.get_story_metrics(written_raw, story_prompts)
        print(f"DEBUG MAIN - Metrics: {metrics}")
        
        # Save the story to database
        story_id = db.add_story(title, written_raw, story_prompts, metrics['word_count'], metrics['points'], username)
        
        if story_id:
            print(f"DEBUG MAIN - Story saved successfully with ID: {story_id}")
            
            # Clear the used prompts from session after successful save
            session.pop('current_prompts', None)
            
            return render_template("congrats.html", title=title, story_len=metrics['word_count'], points=metrics['points'], words=metrics['num_used_prompts'])
        
        else:
            print("DEBUG MAIN - Story save failed")
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
        
        # Get user's stories and find the specific one by title
        stories = db.get_user_stories(username)
        story = None
        
        for s in stories:
            if s['title'] == story_title:
                story = s
                break
        
        # If story not found, redirect to prior pieces with error message
        if not story:
            print(f"[ Error ] Story '{story_title}' not found.")
            return redirect(url_for("prior_pieces"))

        return render_template("read-story.html", story=story)
    
    except Exception as e:
        print(f"Error reading story: {e}")
        return redirect(url_for("prior_pieces"))

# Test route for debugging database connection and operations
@app.route('/test-db')
@login_required
def test_db():
    """Test database connection and basic operations for debugging purposes"""
    try:
        # Test connection
        connection_test = db.test_connection()
        
        # Get current user
        username = session.get('username')
        user = db.get_user(username)
        
        # Test story insertion with minimal data
        test_prompts = {
            "name": "Test Name",
            "job": "Test Job", 
            "location": "Test Place",
            "object": "Test Object",
            "bonus": "Test Bonus"
        }
        
        story_id = db.add_story(
            title="Test Story",
            story_content="This is a test story to verify database functionality.",
            prompts=test_prompts,
            word_count=10,
            points_earned=5,
            username=username
        )
        
        return f"""
        <h2>Database Test Results</h2>
        <p>Connection Test: {'PASS' if connection_test else 'FAIL'}</p>
        <p>User Found: {'PASS' if user else 'FAIL'}</p>
        <p>Story Insert: {'PASS' if story_id else 'FAIL'}</p>
        <p>Story ID: {story_id}</p>
        <p>User Data: {user}</p>
        """
        
    except Exception as e:
        return f"<h2>Database Test Error</h2><p>{str(e)}</p>"

# logout route
@app.route('/logout')
def logout():
    session.clear() # clear the session data
    return redirect('/login') # redirect to the login page

# mainloop
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)