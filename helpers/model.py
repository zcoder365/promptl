import helpers.database as db

def get_story_length_and_points(story, prompts):
    points = 0
    words_written = len(story) # get story length
    story_text = " ".join(story).upper() # convert story to a list

    # only calculate points if minimum word count is met
    if words_written >= 70:
        # points for each prompt word
        prompt_points = {
            'name': 10,
            'job': 10,
            'object': 10,
            'place': 10,
            'bonus': 20
        }
        
        # check each prompt word
        for prompt_type, word in prompts.items():
            # if the word is in the story...
            if word.upper() in story_text:
                # add the points
                points += prompt_points[prompt_type]
        
    return {"story_length": words_written, "points": points}

def validate_story_input(written: str, title: str, prompts: dict) -> tuple[bool, str]:
    # validate story inputs
    
    if not written or not title:
        return False, "Please provide both story content and title."
        
    if not all(prompts.values()):
        return False, "Missing prompt values."
        
    return True, ""

def process_story_points(story: list, prompts: dict, word_count: int) -> int:
    # calculate points earned for the story
    
    story_info = get_story_length_and_points(story, prompts)
    points_earned = story_info['points']
    
    # Bonus points for stories over 100 words
    if word_count >= 100:
        points_earned += 25
        
    return points_earned

def save_story_to_db(username: str, title: str, content: str, word_count: int, prompts: dict):
    # save the story to the database
    
    story_data = (username, title, content, word_count, str(prompts))
    db.add_story(story_data)