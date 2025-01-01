def calculate_points(prompts, story):
    story = story.lower()
    points = 0
    used_prompts = []
    
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