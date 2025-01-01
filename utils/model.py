def calculate_points(prompts, story):
    story = story.lower()   # make the story lowercase
    points = 0              # keep track of points
    used_prompts = []       # keep track of the used prompts
    
    # only check prompts if the story length is greater than or equal to 70
    if len(story) >= 70:
        # check each prompt
        for prompt_type, prompt in prompts.items():
            if prompt.lower() in story: # check if the prompt is in the story
                points += 10 # add the points
                
                # add the prompt to the used prompts list
                used_prompts.append({
                    "type": prompt_type,
                    "word": prompt
                })
        
        # bonus points for longer stories
        if len(story) >= 100:
            points += 25
    
    return points