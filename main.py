# add allowed hosts for the website
ALLOWED_HOSTS = ['promptl.com', 'www.promptl.com']

# import necessary libraries
from flask import Flask, request, session, redirect, url_for, render_template, flash
from datetime import timedelta
import os
from os import environ as env
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from urllib.parse import quote_plus, urlencode
from jose import jwt
import requests
import utils.prompts as prompts
import utils.model as model
import utils.database as db

# load env file
load_dotenv()

# create the flask app and add configurations
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# set up authentication system
oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

# have a function to get current user's info
def get_current_user():
    token = session.get("user")
    if not token:
        return None
    id_token = token.get("id_token") # Auth0 returns id_token + access_token
    payload = jwt.get_unverified_claims(id_token)
    return {
        "auth0_id": payload["sub"],
        "email": payload.get("email"),
        "name": payload.get("name")
    }

# landing route
@app.route('/')
def index():
    return redirect(url_for("login"))

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        un = request.form['username']
        pw = request.form['password']
        
        # validate user
        user_verified = model.validate_user_login(un, pw)
        if user_verified == True:
            # add username to session
            session['username'] = un
            
            # print(f"User {un} logged in, returning to home page")
            return redirect(url_for("home"))
        
        elif user_verified == False or user_verified == None:
            # print(f"No such user with username {un} exists, sending to sign up...")
            return redirect(url_for("login"))
    
    return render_template("login.html")
    
    # return oauth.auth0.authorize_redirect(
    #     redirect_uri=url_for("callback", _external=True)
    # )

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == "POST":
        un = request.form['username']
        pw = request.form['password']
        
        # determine if user exists
        user_exists = model.validate_user_signup(un, pw)
        if user_exists:
            return redirect(url_for("login"))
        
        added = db.add_user(un, pw)
        if added is None:
            return redirect(url_for("login"))
        
        # add user's username to session and redirect to home page
        session['username'] = un
        return redirect(url_for("home"))
    
    return render_template("signup.html")

# # create a callback route for getting user ifno
# @app.route("/callback", methods=["GET", "POST"])
# def callback():
#     token = oauth.auth0.authorize_access_token()
#     session["user"] = token
#     return redirect(url_for("home")) # redirect user to home page

# home page route
@app.route('/home')
def home():
    # Generate new prompts and store them in session for later use in save_writing
    story_prompts = prompts.gen_all_prompts()
    session['current_prompts'] = story_prompts
        
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
    return render_template('about.html')

# prior pieces route
@app.route('/prior-pieces')
def prior_pieces():
    try:
        user_info = get_current_user()
        user_id = user_info['auth0_id']
        
        if not user_id:
            return redirect(url_for('login'))
        
        # Get user-specific stories from database
        stories = db.get_user_stories(user_id)
        
        return render_template('prior-pieces.html', stories=stories)
    
    except Exception as e:
        print(f"DEBUG MAIN - Error retrieving stories: {e}")
        return render_template('prior-pieces.html', stories=[])

# # user's account page
# @app.route('/my-account')
# def my_account():
#     try:
#         # Get username from session
#         user_token = session['user']
#         if not user_token:
#             return redirect(url_for('login'))
        
#         if not user:
#             return redirect(url_for('login'))
        
#         # Get user's stories to calculate streak
#         stories = db.get_user_stories(username)
#         story_count = len(stories)
        
#         # Handle None values for user stats with proper fallback logic
#         total_words = user.get('total_word_count', 0) or 0
#         points = user.get('points', 0) or 0
        
#         return render_template('my-account.html', 
#                              username=user['username'], 
#                              total_words=total_words, 
#                              points=points, 
#                              streak=story_count)
    
#     except Exception as e:
#         print(f"Error accessing account: {e}")
#         return redirect(url_for('login'))

# save the user's writing
@app.route('/save-writing', methods=['GET', 'POST'])
def save_writing():
    if request.method == "POST":
        # get info from the form
        written_raw = request.form.get('story')
        title = request.form.get('title')
        
        # Validate input data
        if not written_raw or not title:
            return render_template("index.html", message="Please provide both title and story content.")
        
        # get username from session
        username = session['username']
        
        if not username:
            return render_template("index.html", message="User session expired. Please log in again.")
        
        # Get prompts from session instead of relying on global variable
        story_prompts = session.get('current_prompts')
        if not story_prompts:
            print("DEBUG MAIN - No prompts in session, generating new ones")
            story_prompts = prompts.gen_all_prompts()  # Fallback if no prompts in session
        
        # Calculate metrics using the retrieved prompts
        metrics = model.get_story_metrics(written_raw, story_prompts)
        print(f"DEBUG MAIN - Metrics: {metrics}")
        
        # Save the story to database
        story_id = db.add_story(title, written_raw, story_prompts, metrics['word_count'], metrics['points'], username)
        
        if story_id:
            # Clear the used prompts from session after successful save
            session.pop('current_prompts', None)
            
            return render_template("congrats.html", title=title, story_len=metrics['word_count'], points=metrics['points'], words=metrics['num_used_prompts'])
    
    return redirect(url_for("home"))

# read a story page
@app.route("/read-story/<story_title>")
def read_story(story_title):
    try:
        # Get username from session
        user_info = get_current_user()
        user_id = user_info['auth0_id']
        
        if not user_id:
            return redirect(url_for('login'))
        
        # Get user's stories and find the specific one by title
        stories = db.get_user_stories(user_id)
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

# logout route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("index", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

# mainloop
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)