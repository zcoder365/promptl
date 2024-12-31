# general imports
import os
from flask import Flask, request, session, redirect, url_for, render_template
from functools import wraps # preserves function metadata
from flask_sqlalchemy import SQLAlchemy

# import other files
from utils.accounts import *
from utils.prompts import *

# create the flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_URI') # get the URI for the database
db = SQLAlchemy(app) # set up the SQLAlchemy database

# create user database
class User(db.Model):
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# create stories database
class Story(db.Model):
    title = db.Column(db.String(100), unique=True, nullable=False)
    story_content = db.Column(db.String(800), nullable=False)
    author = db.Column(db.String(80), nullable=False)

# create all of the databases
with app.app_context():
    db.create_all()