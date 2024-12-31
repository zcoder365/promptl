# add imports to create the database and handle relationships
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# set up a base
Base = declarative_base()

# create a user model to represent the system's users
class User(Base):
    __tablename__ = "users"
    
    # create a unique identifier for each user
    id = Column(Integer, primary_key=True)
    
    # points earned through writing stories
    points = Column(Integer, default=0)
    
    # parent/guardian email for contact
    parent_email = Column(String)
    
    # current streak of consecutive days with writing stories
    streak = Column(Integer, default=0)
    
    # keep track of the cumulative word count across all stories
    total_word_count = Column(Integer, default=0)
    
    # one user can have many stories
    stories = relationship("Story", back_populates="author")

# create story class to represent the written content
class Story(Base):
    __tablename__ = "stories"
    
    # unique identifier for each story
    id = Column(Integer, primary_key=True)
    
    # writing prompt that inspired the story
    prompt = Column(String)
    
    # number of words in this story
    word_count = Column(Integer)
    
    # foreign key linking to the user who wrote this story
    author_id = Column(Integer, ForeignKey('users.id'))
    
    # many stories can belong to a user/author
    author = relationship("User", back_populates="stories")