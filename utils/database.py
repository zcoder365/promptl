"""Database layer for Promptl - handles all Firestore interactions."""

import os
import json
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth

# load env vars from .env file (only matters locally; render injects them directly)
load_dotenv()

# ─────────────────────────────────────────────────────────────
# FIREBASE INITIALIZATION
# ─────────────────────────────────────────────────────────────
# we use a singleton pattern: initialize firebase once, reuse the connection.
# this matches how you set up lockd in's backend.

_db = None  # module-level cache for the firestore client

def _initialize_firebase():
    """Initialize the firebase admin SDK (only runs once per process)."""
    # firebase_admin tracks initialized apps internally; calling initialize_app
    # twice raises an error, so we check first.
    if not firebase_admin._apps:
        # the credentials JSON is stored as a string in the env var,
        # so we parse it back into a dict before passing to firebase
        cred_json = os.getenv("FIREBASE_CREDENTIALS")
        if not cred_json:
            raise RuntimeError("FIREBASE_CREDENTIALS env var not set!")
        
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)

def get_db():
    """Get the firestore client, initializing firebase if needed."""
    global _db
    if _db is None:
        _initialize_firebase()
        _db = firestore.client()
    return _db

# ─────────────────────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────────────────────

def verify_id_token(id_token: str):
    """Verify a firebase ID token sent from the frontend.
    
    The frontend logs the user in via firebase JS SDK, gets an ID token,
    then sends it to our flask backend. We verify it here to confirm
    the user is who they claim to be.
    
    Args:
        id_token (str): The ID token string from the client.
    
    Returns:
        dict: Decoded token payload with 'uid', 'email', etc., or None if invalid.
    """
    try:
        # 🆕 ensure firebase is initialized before calling auth functions.
        # this matters because verify_id_token() can be called before any
        # firestore operation, so get_db() may not have run yet.
        _initialize_firebase()
        
        # firebase_auth.verify_id_token() does cryptographic verification —
        # it checks the signature, expiration, and issuer. trust this fn.
        decoded = firebase_auth.verify_id_token(id_token)
        return decoded
    except Exception as e:
        print(f"[auth] token verification failed: {e}")
        return None

# ─────────────────────────────────────────────────────────────
# USER OPERATIONS
# ─────────────────────────────────────────────────────────────

def get_or_create_user(uid: str, email: str, display_name: str = None):
    """Fetch a user document, creating it if this is their first login.
    
    Firebase auth handles authentication, but we still need a firestore
    doc for each user to track points, streak, etc.
    
    Args:
        uid (str): Firebase auth user ID.
        email (str): User's email address.
        display_name (str, optional): Display name (from google sign-in).
    
    Returns:
        dict: The user's document data (with their uid included).
    """
    db = get_db()
    user_ref = db.collection("users").document(uid)
    user_doc = user_ref.get()
    
    if user_doc.exists:
        # user already exists — just return their data
        data = user_doc.to_dict()
        data["uid"] = uid
        return data
    
    # first time login — create their doc with default values
    new_user = {
        "email": email,
        "displayName": display_name or email.split("@")[0],
        "createdAt": datetime.now(timezone.utc),
        "totalPoints": 0,
        "totalWords": 0,
        "currentStreak": 0,
        "lastStoryDate": None,  # will be set when they write their first story
    }
    user_ref.set(new_user)
    new_user["uid"] = uid
    return new_user

def get_user(uid: str):
    """Fetch a user document by uid. Returns None if not found."""
    db = get_db()
    user_doc = db.collection("users").document(uid).get()
    if user_doc.exists:
        data = user_doc.to_dict()
        data["uid"] = uid
        return data
    return None

# ─────────────────────────────────────────────────────────────
# STORY OPERATIONS
# ─────────────────────────────────────────────────────────────

def add_story(uid: str, title: str, story_content: str, prompts: dict,
              word_count: int, points_earned: int):
    """Save a new story to firestore + update the user's stats and streak.
    
    Stories are stored as a subcollection under the user, so the path is:
        users/{uid}/stories/{auto-generated story id}
    
    This function does TWO things atomically-ish:
      1. Adds the story document
      2. Updates the parent user doc's totals (points, words) + streak
    
    Args:
        uid (str): The author's firebase uid.
        title (str): Story title.
        story_content (str): The full story text.
        prompts (dict): The prompts that were used.
        word_count (int): Number of words in the story.
        points_earned (int): Points earned for this story.
    
    Returns:
        str: The new story's ID, or None on failure.
    """
    try:
        db = get_db()
        user_ref = db.collection("users").document(uid)
        
        # build the story document
        story_doc = {
            "title": title,
            "content": story_content,
            "prompts": prompts,
            "wordCount": word_count,
            "pointsEarned": points_earned,
            "createdAt": datetime.now(timezone.utc),
        }
        
        # add() generates a unique ID automatically — preferable to set() here
        # because we want firestore to handle ID generation.
        _, story_ref = user_ref.collection("stories").add(story_doc)
        
        # now update the user's running totals + streak
        _update_user_stats_after_story(uid, word_count, points_earned)
        
        return story_ref.id
    except Exception as e:
        print(f"[db] error saving story: {e}")
        return None

def _update_user_stats_after_story(uid: str, word_count: int, points: int):
    """Update user totals + streak after a story is saved.
    
    Streak logic:
      - If they've never written: streak = 1
      - If last story was today: streak unchanged (multiple stories same day = same streak)
      - If last story was yesterday: streak += 1
      - If last story was 2+ days ago: streak resets to 1
    
    Note: this uses UTC dates. for a production app you'd want to use the
    user's local timezone, but UTC is fine for now.
    """
    db = get_db()
    user_ref = db.collection("users").document(uid)
    user = user_ref.get().to_dict()
    
    today = datetime.now(timezone.utc).date()
    last_date = user.get("lastStoryDate")
    
    # firestore returns timestamps as datetime objects — extract just the date part
    if last_date is not None:
        last_date = last_date.date() if hasattr(last_date, "date") else last_date
    
    # figure out the new streak value
    if last_date is None:
        new_streak = 1  # first story ever
    elif last_date == today:
        new_streak = user.get("currentStreak", 1)  # already wrote today, no change
    elif last_date == today - timedelta(days=1):
        new_streak = user.get("currentStreak", 0) + 1  # consecutive day! 🔥
    else:
        new_streak = 1  # streak broken, restart at 1
    
    # firestore.Increment is atomic — safer than read-modify-write for counters
    # (it prevents race conditions if two writes happen at the same time)
    user_ref.update({
        "totalPoints": firestore.Increment(points),
        "totalWords": firestore.Increment(word_count),
        "currentStreak": new_streak,
        "lastStoryDate": datetime.now(timezone.utc),
    })

def get_user_stories(uid: str):
    """Fetch all stories for a user, newest first.
    
    Returns:
        list: List of story dicts (with 'id' field added). Empty list on error.
    """
    try:
        db = get_db()
        stories_ref = (
            db.collection("users")
            .document(uid)
            .collection("stories")
            .order_by("createdAt", direction=firestore.Query.DESCENDING)
        )
        stories = []
        for doc in stories_ref.stream():
            data = doc.to_dict()
            data["id"] = doc.id  # include the doc ID so we can link to it
            stories.append(data)
        return stories
    except Exception as e:
        print(f"[db] error fetching stories for {uid}: {e}")
        return []

def get_story(uid: str, story_id: str):
    """Fetch a single story by ID (only if it belongs to the given user).
    
    Scoping the lookup under the user's subcollection means we automatically
    can't accidentally return another user's story. ✨
    """
    try:
        db = get_db()
        doc = (
            db.collection("users")
            .document(uid)
            .collection("stories")
            .document(story_id)
            .get()
        )
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None
    except Exception as e:
        print(f"[db] error fetching story {story_id}: {e}")
        return None