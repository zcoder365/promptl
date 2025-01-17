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
    with open("text/" + file_name, "r") as f:
        data = f.read()
        data2 = data.replace("\n", ",").split(',')
        
    prompt = random.choice(data2)
    return prompt.upper()

# generate all the prompts using all the files
def gen_all_prompts():
    # keep track of prompts
    prompts = {}
    
    # generate prompts for the dict
    prompts['name'] = gen_prompt(NAMES_FILE)
    prompts['job'] = gen_prompt(JOBS_FILE)
    prompts['object'] = gen_prompt(OBJECTS_FILE)
    prompts['location'] = gen_prompt(PLACES_FILE)
    prompts['bonus'] = gen_prompt(BONUS_FILE)
    
    # return the prompts
    return prompts

# generate a compliment for the results page
def gen_compliment():
	compliments = ['Great Job!', 'Excellent Work!', 'Super Job!', 'Way to Go!']

	return random.choice(compliments)