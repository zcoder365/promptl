import os
from datetime import datetime

def calculate_points(prompts, story):
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
    """Calculate word count and points for the story"""
    
    word_count = len(written_raw.split())
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