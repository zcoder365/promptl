import os
from datetime import datetime

def calculate_points(prompts, story):
    # set vars to keep track of story, points, and used prompts
    story = story.lower() # convert story to lowercase
    points = 0 # initialize points
    used_prompts_count = 0 # initialize used prompts count
    
    # check if the story is empty
    if not story:
        return {
            "story": "",
            "points": 0,
            "num_used_prompts": 0
        }
        
    elif len(story) < 70: # if the story is less than 70 characters, return 0 points
        return {
            "story": story,
            "points": 0,
            "num_used_prompts": 0
        }
        
    elif len(story) >= 70: # only calculate score if len(story) ≥ 70
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
    
    # create a dictionary to store the results
    results = {
        "story": story,
        "points": 0,
        "num_used_prompts": 0
    }
    
    results["points"] = points
    results["num_used_prompts"] = used_prompts_count
    
    # return the points earned from writing the story
    return results

def validate_writing_input(written_raw, title) -> bool:
    """Validate that all required fields are present"""
    
    if not all([written_raw, title]):
        return False
    
    return True

def get_story_metrics(written_raw, prompts):
    """Calculate word count and points for the story"""
    
    word_count = len(written_raw.split()) # count the words in the story
    story_results = calculate_points(prompts, written_raw) # calculate the points for the used words in the story
    
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