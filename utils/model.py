import os
from datetime import datetime
from utils.database import add_user, find_user

def calculate_points(prompts, story):
    """Calculate points earned for a story based on prompt usage and length.
    
    Evaluates whether prompts are used in the story and awards points accordingly:
    - 10 points per regular prompt (name, job, object, location) used
    - 20 points for bonus prompt if used
    - 25 bonus points if story length >= 100 characters
    - 0 points if story length < 70 characters
    
    Args:
        prompts (dict): Dictionary containing prompt keys ('name', 'job', 'object', 'location', 'bonus')
                       and their corresponding prompt values.
        story (str): The story text to evaluate.
    
    Returns:
        dict: Contains keys 'story', 'points', and 'num_used_prompts' with their calculated values.
    """
    # set vars to keep track of story, points, and used prompts
    story_lower = story.lower() # convert story to lowercase
    points = 0 # initialize points
    used_prompts_count = 0 # initialize used prompts count
        
    if len(story) >= 70: # only calculate score if len(story) ≥ 70
        # check each prompt
        for prompt_type, prompt in prompts.items():
            if prompt.lower() in story_lower: # check if the prompt is in the story
                if prompt_type == "bonus":
                    points += 20
                
                elif prompt_type != "bonus":
                    points += 10
                
                # add one to the count of used prompts
                used_prompts_count += 1
        
        # bonus points for longer stories
        if len(story) >= 100:
            points += 25
        
        results = {
            "story": story,
            "points": points,
            "num_used_prompts": used_prompts_count
        }
            
    else:
        results = {
            "story": story,
            "points": 0,
            "num_used_prompts": 0
        }
        
    print(f"Debugging - Points earned: {results['points']}")
    
    # return the points earned from writing the story
    return results

def get_story_metrics(written_raw, prompts):
    """Calculate word count and points for the story.
    
    Args:
        written_raw (str): The raw story text.
        prompts (dict): Dictionary containing all story prompts.
    
    Returns:
        dict: Contains 'word_count', 'points', and 'num_used_prompts' metrics.
    """
    word_count = len(written_raw.split())
    story_results = calculate_points(prompts, written_raw)
    
    return {
        'word_count': word_count,
        'points': story_results['points'],
        'num_used_prompts': story_results['num_used_prompts']
    }

def create_story_document(title, written_raw, prompts, metrics, user_id):
    """Create a new story document for database insertion.
    
    Args:
        title (str): The title of the story.
        written_raw (str): The full story content.
        prompts (dict): Dictionary of prompts used in the story.
        metrics (dict): Dictionary containing word_count and points.
        user_id: The ID of the story author (currently unused).
    
    Returns:
        dict: A story document containing title, content, prompts, metrics, and timestamp.
    """
    return {
        "title": title,
        "story_content": written_raw,
        "prompt": prompts,
        "word_count": metrics['word_count'],
        "points": metrics['points'],
        # "author_id": user_id,
        "created_at": datetime.now()
    }
    
# def validate_user_login(username: str, password: str):
#     # find user and validate them
#     user = find_user(username)
#     if user: 
#         # compare passwords
#         if password == user["password"]:
#             return True
    
#     return False

# def validate_user_signup(username: str, password: str):
#     pass