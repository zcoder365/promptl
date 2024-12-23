def get_story_length_and_points(story, prompts):
    points = 0
    words_written = len(story) # get story length
    story_text = " ".join(story).upper() # convert story to a list

    if words_written >= 70:
        if prompts['name'] in story_text:
            points += 10
            words_used += 1
        
        if prompts['job'] in story_text:
            points += 10
            words_used += 1
        
        if prompts['object'] in story_text:
            points += 10
            words_used += 1
        
        if prompts['place'] in story_text:
            points += 10
            words_used += 1
        
        if prompts['bonus'] in story_text:
            points += 20
            words_used += 1
        
    return {"story_length": words_written, "points": points}