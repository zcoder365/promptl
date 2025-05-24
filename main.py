# add allowed hosts for the website
ALLOWED_HOSTS = ['promptl.com', 'www.promptl.com']

# import necessary libraries
from functools import wraps
from flask import Flask, request, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
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
prompts = prompts.gen_all_prompts()

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
        
        if len(username) < 3:
            return render_template("signup.html", message="Username must be at least 3 characters.")
        
        # see if the user already exists
        user = db.get_user(username)
        
        # if the user already exists, return error message
        if user:
            return render_template("signup.html", message="Username already exists.")
        
        # if the user doesn't exist, create a new user
        else:
            # hash the password
            hashed_password = generate_password_hash(password)
            
            # add the user to the database
            db.add_user(username, hashed_password)
            
            # redirect to login page
            return redirect(url_for('login'))
    
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
            
            # Get user ID
            try:
                user_id = ObjectId(session.get('user_id'))
            except:
                return render_template("index.html", message="User session expired. Please log in again.")
            
            # Process story metrics
            metrics = model.get_story_metrics(written_raw, prompts)
            
            # Create and save story
            story_doc = model.create_story_document(title, written_raw, prompts, metrics, user_id)
            
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