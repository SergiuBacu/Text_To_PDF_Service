from flask_login import UserMixin
from pip._vendor.distlib import database

from . import database

class User(UserMixin, database.Model):
    id = database.Column(database.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = database.Column(database.String(100), unique=True)
    password = database.Column(database.String(100))
    name = database.Column(database.String(1000))
    files = database.relationship('File', back_populates='user')

class File(database.Model):
    id = database.Column(database.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    user_id = database.Column(database.Integer, database.ForeignKey('user.id'))
    user = database.relationship('User',back_populates = 'files')
    filename = database.Column(database.String(1000))
    status = database.Column(database.String(100))
    cloud_url = database.Column(database.String(1000))