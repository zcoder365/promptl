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