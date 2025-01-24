from datetime import datetime
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os

def connect_db():
    """Initialize MongoDB connection and return collections"""
    MONGODB_URI = os.getenv("MONGODB_URI")
    
    try:
        client = MongoClient(MONGODB_URI, server_api=ServerApi('1'))
        client.admin.command('ping')
        print("Successfully connected to MongoDB")
        
        db = client['promptl_db']
        return db['users'], db['stories']
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        raise

def calculate_points(prompts: dict, story: str) -> dict:
    # set vars to keep track of story, points, and used prompts
    story = story.lower()
    points = 0
    used_prompts_count = 0
    
    results = {
        "story": story,
        "points": points,
        "num_used_prompts": used_prompts_count
    }
    
    # only calculate score if len(story) ≥ 70
    if len(story) >= 70:
        # check each prompt
        for prompt_type, prompt in prompts.items():
            if prompt.lower() in story: # check if the prompt is in the story
                if prompt_type == "bonus":
                    points += 20
                
                elif prompt_type != "bonus":
                    points += 10
                
                # add one to the count of used prompts
                used_prompts_count += 1
        
        # bonus points for longer stories
        if len(story) >= 100:
            points += 25
    
    results["points"] = points
    results["num_used_prompts"] = used_prompts_count
    
    # return the points earned from writing the story
    return results

def validate_writing_input(written_raw, title):
    """Validate that all required fields are present"""
    if not all([written_raw, title]):
        return False, "Please fill in all required fields (story, title, and prompts)."
    return True, None

def process_story_metrics(written_raw, prompts):
    """Calculate word count and points for the story"""
    story_words = written_raw.split()
    word_count = len(story_words)
    story_results = calculate_points(prompts, written_raw)
    
    return {
        'word_count': word_count,
        'points': story_results['points'],
        'num_used_prompts': story_results['num_used_prompts']
    }

def create_story_document(title, written_raw, prompts, metrics, user_id):
    """Create a new story document for database insertion"""
    return {
        "title": title,
        "story_content": written_raw,
        "prompt": prompts,
        "word_count": metrics['word_count'],
        "points": metrics['points'],
        "author_id": user_id,
        "created_at": datetime.now()
    }

def save_story_to_db(story_doc, user_id, metrics):
    """Save story and update user stats in database"""
    try:
        # Insert story
        story_result = stories_collection.insert_one(story_doc)
        if not story_result.inserted_id:
            raise Exception("Failed to save story to database")
        
        # Update user stats
        user_result = users_collection.update_one(
            {"_id": user_id},
            {
                "$inc": {
                    "total_word_count": metrics['word_count'],
                    "points": metrics['points']
                }
            }
        )
        if user_result.modified_count == 0:
            stories_collection.delete_one({"_id": story_result.inserted_id})
            raise Exception("Failed to update user statistics")
            
        return True, story_doc
        
    except Exception as e:
        return False, str(e)