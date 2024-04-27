from flask import Flask, render_template, redirect, request, url_for, session
from flask_pymongo import PyMongo
import bcrypt
import os
# from bson.objectid import ObjectId
import model
# from pymongo.mongo_client import MongoClient
import pymongo

app = Flask(__name__)

app.secret_key = os.environ["secret_key"]

# uri = 'mongodb+srv://<' + os.environ["mongo_un"] + '>:<' + os.environ["mongo_pw"] + '>@cluster0.usy3a.mongodb.net/?retryWrites=true&w=majority'

uri = "mongodb+srv://" + os.environ['mongo_un'] + ":" + os.environ['mongo_pw'] + "@cluster0.usy3a.mongodb.net/?retryWrites=true&w=majority"

app.config['MONGO_URI'] = uri

app.config['MONGO_DBNAME'] = 'promptl_data'

# mongo = PyMongo(app)
# client = MongoClient(uri)
# data = mongo['promptl_data']
# users = mongo['users']
# writing = mongo['writing']

# client = pymongo.MongoClient(uri, connectTimeoutMS=30000, socketTimeoutMS=None, connect=False, maxPoolsize=1)
# db = client['promptl_data']
# users = db['users']
# writing = db['writing']

client = pymongo.MongoClient(uri)
data = client['promptl_data']

global users
global writing
global title

users = data['users']
writing = data['writing']

name = model.gen_name()
job = model.gen_job()
place = model.gen_place()
object = model.gen_object()
bonus = model.gen_bonus()


@app.route('/')
def index():
	return render_template('login-signup.html')


@app.route('/home')
def home():
	name = model.gen_name()
	job = model.gen_job()
	place = model.gen_place()
	object = model.gen_object()
	bonus = model.gen_bonus()

	global prompts

	prompts = {
	    'name': name,
	    'job': job,
	    'place': place,
	    'object': object,
	    'bonus': bonus
	}

	return render_template('index.html', prompts=prompts)


@app.route('/new-prompt')
def new_prompt():
	return redirect(url_for("home"))


@app.route('/signup-check', methods=['GET', 'POST'])
def signup():
	if request.method == 'POST':
		# users = mongo.db.users
		users = data['users']

		existing_user = users.find_one({'username': request.form['username']})

		un = request.form['username']
		pw = request.form['password']
		parent_email = request.form['parent_email']

		if not existing_user:
			# Create a hash of the user's password
			hashpass = bcrypt.hashpw(request.form['password'].encode('utf–8'),
			                         bcrypt.gensalt())
			users.insert_one({
			    'username': un,
			    'password': str(hashpass, 'utf-8'),
			    'parent_email': parent_email,
			    'points': 0,
			    'streak': 0,
			    "prizes": 0,
			    "average_words": 0
			})
			session['username'] = request.form['username']
			return redirect(url_for('home'))

		return 'That username already exists! Try logging in.'
	return redirect(url_for("home"))


# LOGIN ROUTE
@app.route('/login-check', methods=['GET', 'POST'])
def login():
	if request.method == "POST":
		# users = db['users']
		# users = mongo.db.users
		
		login_user = users.find_one({'username': request.form['username']})
	
		if login_user:
			if bcrypt.checkpw(request.form['password'].encode('utf-8'),
			                  login_user['password'].encode('utf-8')) == True:
				session['username'] = request.form['username']
	
				return redirect(url_for("home"))
	
	return 'Invalid username-password combination. Please try again.'


@app.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('index'))


@app.route('/prior-pieces')
def prior_pieces():
	# writing = client.db.writing

	stories = writing.find({'username': session['username']})

	return render_template('prior-pieces.html', writing=stories)


@app.route('/my-account')
def my_account():
	# users = client.db.users
	# writing = client.db.writing

	username = session['username']

	total_words = 0

	user = users.find_one({'username': username})
	stories = writing.find({'username': username})

	for story in stories:
		word_count = story['word_count']
		total_words += word_count

	return render_template('my-account.html',
	                       users=user,
	                       total_words=total_words)


@app.route('/save-writing', methods=['GET', 'POST'])
def save_writing():
	if request.method == "POST":
		words_used = 0
		points = 0

		# writing = client.db.writing
		# users = client.db.users

		written = request.form['story']
		title = request.form['title'] # assignment of the title...

		user = users.find_one({'username': session['username']})
		userID = user['_id']

		streak = int(user['streak'])
		new_streak = streak + 1

		# Find the user to edit using userID
		myquery = {"_id": PyMongo.ObjectId(userID)} # ObjectId not defined - FIGURE THIS OUT
		# Create new values to update the user
		new_streak = {"$set": {'streak': new_streak}}

		# Update the selected user and assign new values
		users.update_one(myquery, new_streak)

		# prompts = prompts

		writing.insert_one({"prompts": prompts})
		prompt_id = writing['_id']

		story = written.split(' ')
		words_written = len(story)

		if words_written >= 70:
			if prompts['name'] in written.upper():
				# points = user['points']
				points += 10

				words_used += 1

				# myquery = {"_id":ObjectId(userID)}
				# new_points = {"$set":{'points':points}}
				# users.update_one(myquery, new_points)

			elif prompts['name'] not in written.upper():
				pass

			if prompts['job'] in written.upper():
				# points = user['points']
				points += 10

				words_used += 1

				# myquery = {"_id":ObjectId(userID)}
				# new_points = {"$set":{'points':points}}
				# users.update_one(myquery, new_points)

			elif prompts['job'] not in written.upper():
				pass

			if prompts['object'] in written.upper():
				# points = user['points']
				points += 10

				words_used += 1

			elif prompts['object'] not in written.upper():
				pass

			if prompts['place'] in written.upper():
				# points = user['points']
				points += 10

				words_used += 1

			elif prompts['place'] not in written.upper():
				pass

			if prompts['bonus'] in written.upper():
				# points = user['points']
				points += 20

				words_used += 1

			elif prompts['bonus'] not in written.upper():
				pass

		story = written.upper()
		story = story.split()
		story_word_count = int(len(story))

		title = request.form['title'] # referenced before assignment; but this is the assignment...

		if story_word_count >= 100:
			points += 25

		writing.insert_one({
		    'title': title,
		    'story': written,
		    'username': session['username'],
		    'word_count': story_word_count,
		    "prompts": prompts,
		    "points": points
		})

		story = writing.find_one({'title': title})

		words = words_used

		compliment = model.gen_compliment()

		user = users.find_one({"_id": ObjectId(userID)})
		user_points = user['points']
		user_points = int(user_points)

		add_points = points + user_points

		myquery = {"_id": ObjectId(userID)}
		new_points = {"$set": {'points': add_points}}
		users.update_one(myquery, new_points)

	return render_template("congrats.html", title=title, story=story, words=words, written=story_word_count, compliment=compliment, points=points)


@app.route("/my-account/edit")
def edit_info():
	# users = client.db.users
	username = session['username']
	user = users.find_one({'username': username})
	return render_template("edit-info.html", user=user)


@app.route('/change-email/<userID>', methods=['POST', 'GET'])
def save_info(userID):
	# users = client.db.users

	parent_email = request.form['changed']

	# Find the user to edit using userID
	myquery = {"_id": ObjectId(userID)}
	# Create new values to update the user
	newvalues = {"$set": {'parent_email': parent_email}}

	# Update the selected user and assign new values
	users.update_one(myquery, newvalues)

	# Find the newly edited user
	users = users.find_one({'_id': ObjectId(userID)})

	return redirect(url_for('my_account'))

@app.route("/read-story/<storyID>")
def read_story(storyID):
	# writing = client.db.writing

	story = writing.find_one({"_id": ObjectId(storyID)})

	return render_template("read-story.html", story=story)


@app.route("/edit-story/<storyID>")
def edit_story(storyID):
	writing = mongo.db.writing

	story = writing.find_one({"_id": ObjectId(storyID)})

	return render_template("edit-story.html", story=story)


@app.route('/update-story/<storyID>')
def update_story(storyID):
	if request.method == "POST":
		writing = mongo.db.writing

		story = request.form['updated_story']

		myquery = {"_id": ObjectId(storyID)}
		newvalues = {"$set": {'story': story}}

		writing.update_one(myquery, newvalues)

	return redirect(url_for('prior_pieces'))


@app.route('/send-stats/<storyID>')
def send_stats(storyID):
	users = mongo.db.users
	writing = mongo.db.writing

	username = session['username']

	users = users.find_one({"username": username})
	story = writing.find_one({"_id": ObjectId(storyID)})

	title = story['title']
	points = story['points']
	words = story['word_count']

	parent = users['parent_email']

	message = "Hello Parent!\n" + username + " wrote a story titled " + title + ' that was ' + str(
	    words) + 'long! They earned ' + str(points) + " points for this story!"

	context = ssl.create_default_context()

	try:
		server = smtplib.SMTP(smtp_server, port)
		server.ehlo()  # Can be omitted
		server.starttls(context=context)  # Secure the connection
		server.ehlo()  # Can be omitted
		server.login(sender_email, password)
		with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
			# server.ehlo()
			server.starttls(context=context)
			# server.ehlo()
			server.login(sender_email, password)
			server.sendmail(sender_email, parent, message)

			server.quit()

	except Exception as e:
		# Print any error messages to stdout
		print(e)

	return redirect(url_for('prior_pieces'))

@app.route('/about')
def about_page():
	return render_template('about.html')

# # Words Written in the Story
# @app.route("/word-count")
# def words_written():
# 	get_words = request.form['story']
# 	story_lenth = list(words)
# 	words = story_length.split(" ")
# 	words = len(words)
# 	return words

app.run(host="0.0.0.0", port=8080)