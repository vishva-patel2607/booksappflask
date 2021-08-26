from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import uuid
from  werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta,date
from flask_cors import CORS
from sqlalchemy import or_
import os










db = SQLAlchemy()



def setup_db(app):
    database_name ='booksapp'
    default_database_path= "postgres://{}:{}@{}/{}".format('postgres', 'VPp@26072000', 'localhost:5432', database_name)
    database_path = os.getenv('DATABASE_URL', default_database_path)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config['SECRET_KEY'] = "patel gang"
    db.app = app
    db.init_app(app)



def db_drop_and_create_all():
    db.drop_all()
    db.create_all()



class userModel(db.Model):
    __tablename__ = 'booksapp_users'
    usernumber = db.Column(db.BigInteger, primary_key=True)
    username  = db.Column(db.String(50),nullable=False,unique=True)
    password = db.Column(db.String(200),nullable=False)
    email = db.Column(db.String(100),nullable=False,unique=True)
    firstname = db.Column(db.String(20),nullable=False)
    lastname = db.Column(db.String(20),nullable=False)
    dob = db.Column(db.Date,nullable=False)
    phonenumber = db.Column(db.String(20),nullable=False)


    def __init__(self, username, password,email , firstname, lastname, dob, phonenumber):
        self.username = usename
        self.password = password
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.dob = dob
        self.phonenumber = phonenumber


    def details(self):
        return {
            'usernumber': self.usernumber,
            'username': self.username,
            'password': self.password,
            'email': self.email,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'dob': self.dob,
            'phonenumber': self.phonenumber
        }

    def insert(self):
        db.session.add(self)
        db.session.commit()



    def delete(self):
        db.session.delete(self)
        db.session.commit()



    def update(self):
        db.session.commit()