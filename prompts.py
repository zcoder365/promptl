import random

prompt_file_names = ["bonus.txt", "jobs.txt", "names.txt", "objects.txt", "places.txt"]

def gen_prompt(file_name):
    with open("text/" + file_name, "r") as f:
        data = f.read()
        data2 = data.replace("\n", ",").split(',')
        
    prompt = random.choice(data2)
    return prompt.upper()

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