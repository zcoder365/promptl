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

def gen_name():
	with open("text/names.txt", "r") as f:
		data = f.read()
		names = data.replace("\n", ",").split(',')
        
	name = random.choice(names)
	return name.upper()
        

def gen_job():
	with open("text/jobs.txt", "r") as f:
		data = f.read()
		jobs = data.replace("\n", ",").split(',')
        
	name = random.choice(jobs)
	return name.upper()

def gen_object():
	objects = []

	object_file = open('text/objects.txt', 'r')
	object_data = object_file.read()
	objects = object_data.replace('\n', ',').split(",")

	object = random.choice(objects)
	object = object.upper()

	return object

def gen_place():
	places = []

	place_file = open('text/places.txt', 'r')
	place_data = place_file.read()
	places = place_data.replace('\n', ",").split(",")
	
	place = random.choice(places)
	place = place.upper()

	return place

def gen_bonus():
	bonus = []
	
	bonus_file = open('text/bonus.txt', 'r')
	bonus_data = bonus_file.read()
	bonus = bonus_data.replace('\n', ',').split(",")
	
	bonus = random.choice(bonus)
	bonus = bonus.upper()

	return bonus

def gen_compliment():
	compliments = ['Great Job!', 'Excellent Work!', 'Super Job!', 'Way to Go!']

	compliment = random.choice(compliments)

	return compliment