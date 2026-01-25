import random

# set the file names for the prompts
BONUS_FILE = "bonus.txt"
JOBS_FILE = "jobs.txt"
NAMES_FILE = "names.txt"
OBJECTS_FILE = "objects.txt"
PLACES_FILE = "places.txt"

# set the prompt file names as an array
prompt_file_names = [BONUS_FILE, JOBS_FILE, NAMES_FILE, OBJECTS_FILE, PLACES_FILE]

# generate a single prompt using a specific file
def gen_prompt(file_name):
    """Generate a random prompt from a specified text file.
    
    Args:
        file_name (str): Name of the text file containing prompts.
    
    Returns:
        str: A randomly selected prompt in uppercase.
    """
    with open("text/" + file_name, "r") as f:
        data = f.read()
        data2 = data.replace("\n", ",").split(',')
        
    prompt = random.choice(data2)
    return prompt.upper()

# generate all the prompts using all the files
def gen_all_prompts():
    """Generate all writing prompts from their respective files.
    
    Generates one prompt each for name, job, object, location, and bonus categories
    by randomly selecting from their corresponding text files.
    
    Returns:
        dict: Dictionary containing keys 'name', 'job', 'object', 'location', 'bonus',
              each with a randomly selected prompt value in uppercase.
    """
    # keep track of prompts
    story_prompts = {}
    
    # generate prompts for the dict
    story_prompts['name'] = gen_prompt(NAMES_FILE)
    story_prompts['job'] = gen_prompt(JOBS_FILE)
    story_prompts['object'] = gen_prompt(OBJECTS_FILE)
    story_prompts['location'] = gen_prompt(PLACES_FILE)
    story_prompts['bonus'] = gen_prompt(BONUS_FILE)
    
    # return the prompts
    return story_prompts

# generate a compliment for the results page
def gen_compliment():
    """Generate a random compliment for display on the results page.
    
    Returns:
        str: A randomly selected compliment message.
    """
    compliments = ['Great Job!', 'Excellent Work!', 'Super Job!', 'Way to Go!']

    return random.choice(compliments)