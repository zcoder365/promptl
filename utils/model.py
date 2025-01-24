def calculate_points(prompts: dict, story: str) -> dict:
    story = story.lower() # make the story lowercase
    points = 0 # keep track of points
    used_prompts_count = 0 # keep track of the used prompts
    
    results = {
        "story": story,
        "points": points,
        "num_used_prompts": used_prompts_count
    }
    
    # only calculate score if len(story) ≥ 70
    if len(story) >= 70:
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
    
    # return the points earned from writing the story
    return results