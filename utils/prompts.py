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
    prompts = {}
    
    # add keys to the prompts dict to be able to generate the variables
    for file in prompt_file_names:
        if "bonus" in file:
            key = "bonus"
        elif "jobs" in file:
            key = "job"
        elif "names" in file:
            key = "name"
        elif "objects" in file:
            key = "object"
        elif "places" in file:
            key = "place"
        
        # generate the prompts using the gen_prompt()  function
        prompts[key] = gen_prompt(file)
    
    # return the prompts
    return prompts

# generate a compliment for the results page
def gen_compliment():
	compliments = ['Great Job!', 'Excellent Work!', 'Super Job!', 'Way to Go!']

	return random.choice(compliments)