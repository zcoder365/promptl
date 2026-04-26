"""Story scoring + metrics calculations for Promptl."""

# note: we removed the old user validation functions (validate_user_login, etc.)
# because firebase auth now handles all authentication. ✨

def calculate_points(prompts, story):
    """Calculate points earned for a story based on prompt usage and length.
    
    Scoring rules:
      - story must be at least 70 chars long to earn ANY points
      - 10 points per regular prompt (name, job, object, location) used
      - 20 points for the bonus prompt if used
      - 25 bonus points if story is at least 100 chars
    
    Args:
        prompts (dict): Dict with keys 'name', 'job', 'object', 'location', 'bonus'.
        story (str): The story text to evaluate.
    
    Returns:
        dict: Contains 'story', 'points', and 'num_used_prompts'.
    """
    # convert story to lowercase once so we can do case-insensitive matching
    story_lower = story.lower()
    points = 0
    used_prompts_count = 0
    
    # only score stories that meet the minimum length
    if len(story) >= 70:
        # check each prompt to see if it appears in the story
        for prompt_type, prompt in prompts.items():
            if prompt.lower() in story_lower:
                # bonus word is worth double
                if prompt_type == "bonus":
                    points += 20
                else:
                    points += 10
                
                used_prompts_count += 1
        
        # extra reward for longer stories
        if len(story) >= 100:
            points += 25
        
        results = {
            "story": story,
            "points": points,
            "num_used_prompts": used_prompts_count
        }
    else:
        # story too short — no points awarded
        results = {
            "story": story,
            "points": 0,
            "num_used_prompts": 0
        }
    
    print(f"[scoring] Points earned: {results['points']}")
    
    return results


def get_story_metrics(written_raw, prompts):
    """Calculate word count + points for a story in one call.
    
    This is the convenience function that main.py calls before saving.
    
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