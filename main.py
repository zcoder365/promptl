"""Promptl Flask backend — routes for prompts, stories, and auth."""

from flask import Flask, request, session, redirect, url_for, render_template, jsonify
from datetime import timedelta
import os
from dotenv import load_dotenv

import utils.prompts as prompts
import utils.model as model
import utils.database as db

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # keep users logged in for a week

# ─────────────────────────────────────────────────────────────
# AUTH HELPER
# ─────────────────────────────────────────────────────────────

def get_current_user():
    """Get the currently logged-in user from session, or None."""
    uid = session.get("uid")
    if not uid:
        return None
    return db.get_user(uid)

def require_login(view_func):
    """Decorator: redirect to login if user isn't authenticated."""
    from functools import wraps
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("uid"):
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)
    return wrapper

# ─────────────────────────────────────────────────────────────
# PUBLIC ROUTES
# ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    """Landing — redirect to home if logged in, else login page."""
    if session.get("uid"):
        return redirect(url_for("home"))
    return redirect(url_for("login"))

@app.route('/login')
def login():
    """Show the login page (frontend handles firebase auth)."""
    return render_template("login.html")

@app.route('/signup')
def signup():
    """Show the signup page."""
    return render_template("signup.html")

@app.route('/auth/session', methods=['POST'])
def create_session():
    """Receive a firebase ID token from frontend, verify it, and set session.
    
    Flow: user logs in via firebase JS SDK on the frontend → frontend gets
    an ID token → POSTs it here → we verify it → we set a flask session cookie.
    
    From this point on, the user is "logged in" to flask, and we can use
    session['uid'] to identify them on every request.
    """
    data = request.get_json()
    id_token = data.get("idToken")
    
    if not id_token:
        return jsonify({"error": "missing idToken"}), 400
    
    # verify the token cryptographically with firebase
    decoded = db.verify_id_token(id_token)
    if not decoded:
        return jsonify({"error": "invalid token"}), 401
    
    # token is valid — extract user info and create/fetch their firestore doc
    uid = decoded["uid"]
    email = decoded.get("email", "")
    display_name = decoded.get("name")  # populated for google sign-in
    
    db.get_or_create_user(uid, email, display_name)
    
    # set flask session — this cookie keeps them logged in across requests
    session.permanent = True
    session["uid"] = uid
    
    return jsonify({"success": True})

@app.route('/logout')
def logout():
    """Clear flask session (frontend should also call firebase signOut)."""
    session.clear()
    return redirect(url_for("login"))

# ─────────────────────────────────────────────────────────────
# PROTECTED ROUTES (require login)
# ─────────────────────────────────────────────────────────────

@app.route('/home')
@require_login
def home():
    """Home page — generates fresh prompts and shows the writing form."""
    story_prompts = prompts.gen_all_prompts()
    session['current_prompts'] = story_prompts
    
    return render_template(
        'index.html',
        name=story_prompts['name'],
        job=story_prompts['job'],
        place=story_prompts['location'],
        object=story_prompts['object'],
        bonus=story_prompts['bonus'],
    )

@app.route('/new-prompt')
@require_login
def new_prompt():
    """Reload home to get fresh prompts."""
    return redirect(url_for("home"))

@app.route('/about')
def about_page():
    """About page (public — no login required)."""
    return render_template('about.html')

@app.route('/save-writing', methods=['POST'])
@require_login
def save_writing():
    """Process a submitted story: calculate metrics, save to db, show congrats."""
    written_raw = request.form.get('story', '').strip()
    title = request.form.get('title', '').strip()
    
    if not written_raw or not title:
        return redirect(url_for("home"))
    
    # get the prompts that were active when the user started writing
    # (we stored them in session when home loaded)
    story_prompts = session.get('current_prompts')
    if not story_prompts:
        # fallback shouldn't normally happen, but just in case
        story_prompts = prompts.gen_all_prompts()
    
    # calculate word count + points
    metrics = model.get_story_metrics(written_raw, story_prompts)
    
    # save to firestore (also updates user stats + streak)
    uid = session["uid"]
    db.add_story(
        uid=uid,
        title=title,
        story_content=written_raw,
        prompts=story_prompts,
        word_count=metrics['word_count'],
        points_earned=metrics['points'],
    )
    
    # clear the prompts so reloading congrats doesn't reuse them
    session.pop('current_prompts', None)
    
    return render_template(
        "congrats.html",
        title=title,
        story_len=metrics['word_count'],
        points=metrics['points'],
        words=metrics['num_used_prompts'],
        compliment=prompts.gen_compliment(),
    )

@app.route('/prior-pieces')
@require_login
def prior_pieces():
    """Show a read-only archive of the user's past stories."""
    raw_stories = db.get_user_stories(session["uid"])
    
    # transform firestore's camelCase fields into snake_case for templates.
    # this keeps templates clean (no knowledge of db field names) and
    # consistent with my-account.html's variable style.
    stories = [
        {
            "id": s.get("id"),
            "title": s.get("title"),
            "word_count": s.get("wordCount", 0),
            "points_earned": s.get("pointsEarned", 0),
            "created_at": s.get("createdAt"),
        }
        for s in raw_stories
    ]
    
    return render_template("prior-pieces.html", stories=stories)

@app.route('/read-story/<story_id>')
@require_login
def read_story(story_id):
    """Show a single story (read-only)."""
    raw_story = db.get_story(session["uid"], story_id)
    if not raw_story:
        return redirect(url_for("prior_pieces"))
    
    # transform firestore's camelCase to snake_case for the template
    story = {
        "id": raw_story.get("id"),
        "title": raw_story.get("title"),
        "content": raw_story.get("content"),
        "word_count": raw_story.get("wordCount", 0),
        "points_earned": raw_story.get("pointsEarned", 0),
        "prompts": raw_story.get("prompts", {}),
        "created_at": raw_story.get("createdAt"),
    }
    
    return render_template("read-story.html", story=story)

@app.route('/my-account')
@require_login
def my_account():
    """User's profile page with stats."""
    user = get_current_user()
    if not user:
        return redirect(url_for("login"))
    
    return render_template(
        "my-account.html",
        username=user.get("displayName", "Friend"),
        streak=user.get("currentStreak", 0),
        points=user.get("totalPoints", 0),
        total_words=user.get("totalWords", 0),
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)