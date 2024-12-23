import random

BONUS_FILE = "bonus.txt"
JOBS_FILE = "jobs.txt"
NAMES_FILE = "names.txt"
OBJECTS_FILE = "objects.txt"
PLACES_FILE = "places.txt"

prompt_file_names = [BONUS_FILE, JOBS_FILE, NAMES_FILE, OBJECTS_FILE, PLACES_FILE]

def gen_prompt(file_name):
    with open("text/" + file_name, "r") as f:
        data = f.read()
        data2 = data.replace("\n", ",").split(',')
        
    prompt = random.choice(data2)
    return prompt.upper()

def gen_all_prompts():
    prompts = {}
    
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
        
        prompts[key] = gen_prompt(file)
        
    return prompts

def gen_compliment():
	compliments = ['Great Job!', 'Excellent Work!', 'Super Job!', 'Way to Go!']

	compliment = random.choice(compliments)

	return compliment