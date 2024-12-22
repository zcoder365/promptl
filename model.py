def get_story_length_and_points(story, prompts):
    points = 0
    words_used = 0 # was referenced, but never created
    
    # get it's length/number of words
    words_written = len(story)
    story_text = " ".join(story).upper() # need to fix the story checking since it's a list, not a string

    if words_written >= 70:
        if prompts['name'] in story_text:
            points += 10
            words_used += 1
            
        elif prompts['name'] not in story_text:
            pass
        
        if prompts['job'] in story_text:
            points += 10
            
            words_used += 1

        elif prompts['job'] not in story_text:
            pass
        
        if prompts['object'] in story_text:
            points += 10
            words_used += 1
            
        elif prompts['object'] not in story_text:
            pass
        
        if prompts['place'] in story_text:
            points += 10
            words_used += 1
            
        elif prompts['place'] not in story_text:
            pass
        
        if prompts['bonus'] in story_text:
            points += 20
            words_used += 1
            
        elif prompts['bonus'] not in story_text:
            pass
        
    return {"story_length": words_written, "points": points}