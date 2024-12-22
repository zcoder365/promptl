def get_story_length_and_points(story, prompts):
    points = 0
    words_used = 0 # was referenced, but never created
    
    # get it's length/number of words
    words_written = len(story)

    if words_written >= 70:
        if prompts['name'] in story.upper():
            points += 10
            words_used += 1
            
        elif prompts['name'] not in story.upper():
            pass
        
        if prompts['job'] in story.upper():
            points += 10
            
            words_used += 1

        elif prompts['job'] not in story.upper():
            pass
        
        if prompts['object'] in story.upper():
            points += 10
            words_used += 1
            
        elif prompts['object'] not in story.upper():
            pass
        
        if prompts['place'] in story.upper():
            points += 10
            words_used += 1
            
        elif prompts['place'] not in story.upper():
            pass
        
        if prompts['bonus'] in story.upper():
            points += 20
            words_used += 1
            
        elif prompts['bonus'] not in story.upper():
            pass
        
    return {"story_length": words_written, "points": points}