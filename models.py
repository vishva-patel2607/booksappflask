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
from geoalchemy2.types import Geometry










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
        self.username = username
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



class bookModel(db.Model):
    __tablename__ = 'booksapp_book'
    book_id = db.Column(db.BigInteger, primary_key=True)
    book_name  = db.Column(db.String(50),nullable=False)
    book_year = db.Column(db.Integer,nullable=False)
    book_condition = db.Column(db.String(10),nullable=False)
    book_img = db.Column(db.String(200),nullable=False)
    book_price = db.Column(db.BigInteger,nullable=False)
    store_id = db.Column(db.BigInteger,nullable=False)
    usernumber = db.Column(db.BigInteger,nullable=False)
    book_author = db.Column(db.String(20),nullable=False)

    def __init__(self, book_name, book_year,book_condition , book_img, book_price, store_id, usernumber,book_author): 
        self.book_name  = book_name
        self.book_year = book_year
        self.book_condition = book_condition
        self.book_img = book_img
        self.book_price = book_price
        self.store_id = store_id
        self.usernumber = usernumber
        self.book_author = book_author

    def details(self):
        return {
            "book_id" : self.book_id,
            "book_name"  : self.book_name,
            "book_year" : self.book_year,
            "book_condition" : self.book_condition,
            "book_img" : self.book_img,
            "book_price" : self.book_price, 
            "store_id" : self.store_id,
            "usernumber" : self.usernumber,
            "book_author" : self.book_author
        }

    def insert(self):
        db.session.add(self)
        db.session.commit()



    def delete(self):
        db.session.delete(self)
        db.session.commit()



    def update(self):
        db.session.commit()



class storeModel(db.Model):
    __tablename__ = 'booksapp_store'
    store_id = db.Column(db.BigInteger, primary_key=True)
    usernumber = db.Column(db.BigInteger, nullable=False)
    store_name  = db.Column(db.String(50),nullable=False)
    store_incharge = db.Column(db.String(20))
    store_address = db.Column(db.String(100),nullable=False)
    store_pincode = db.Column(db.String(10),nullable=False)
    store_number = db.Column(db.String(15),nullable=False)
    store_location = db.Column(Geometry(geometry_type='POINT', srid=4326),nullable=False)
    store_latitude = db.Column(db.Float,nullable=False)
    store_longitude = db.Column(db.Float,nullable=False)


    def __init__(self,usernumber, store_name, store_incharge,store_address , store_pincode, store_number, store_location,store_latitude,store_longitude):
        self.usernumber = usernumber
        self.store_name = store_name
        self.store_incharge = store_incharge
        self.store_address = store_address
        self.store_pincode = store_pincode
        self.store_number = store_number
        self.store_location = store_location
        self.store_latitude = store_latitude
        self.store_longitude = store_longitude


    def details(self):
        return {
            'store_id': self.store_id,
            'usernumber': self.usernumber,
            'store_name': self.store_name,
            'store_incharge': self.store_incharge,
            'store_address': self.store_address,
            'store_pincode': self.store_pincode,
            'store_number': self.store_number,
            'store_location': self.store_location,
            'store_latitude': self.store_latitude,
            'store_longitude': self.store_longitude
        }

    def insert(self):
        db.session.add(self)
        db.session.commit()



    def delete(self):
        db.session.delete(self)
        db.session.commit()



    def update(self):
        db.session.commit()


class transactionModel(db.Model):
    __tablename__ = 'booksapp_transaction'
    transaction_id = db.Column(db.BigInteger, primary_key=True)
    book_id  = db.Column(db.BigInteger,nullable=False)
    transaction_status = db.Column(db.String(200),nullable=True)
    lender_id = db.Column(db.BigInteger)
    store_id = db.Column(db.BigInteger)
    borrower_id = db.Column(db.BigInteger)
    lender_transaction_status = db.Column(db.String(20))
    store_transaction_status = db.Column(db.String(20))
    borrower_transaction_status = db.Column(db.String(20))
    book_price = db.Column(db.BigInteger,nullable=False)
    transaction_upload_ts = db.Column(db.DateTime)
    transaction_submit_ts = db.Column(db.DateTime)
    transaction_pickup_ts = db.Column(db.DateTime)
    transaction_return_ts = db.Column(db.DateTime)
    transaction_lenderpickup_ts = db.Column(db.DateTime)


    def __init__(self, book_id, transaction_status,lender_id , store_id, borrower_id, lender_transaction_status, store_transaction_status, borrower_transaction_status, book_price, transaction_upload_ts, transaction_submit_ts, transaction_pickup_ts, transaction_return_ts, transaction_lenderpickup_ts): 
        self.book_id  = book_id
        self.transaction_status = transaction_status
        self.lender_id = lender_id
        self.store_id = store_id
        self.borrower_id = borrower_id
        self.lender_transaction_status = lender_transaction_status
        self.store_transaction_status = store_transaction_status
        self.borrower_transaction_status = borrower_transaction_status
        self.book_price = book_price
        self.transaction_upload_ts = transaction_upload_ts
        self.transaction_submit_ts = transaction_submit_ts
        self.transaction_pickup_ts = transaction_pickup_ts
        self.transaction_return_ts = transaction_return_ts
        self.transaction_lenderpickup_ts = transaction_lenderpickup_ts


    def details(self):
        return {
            "transaction_id" : self.transaction_id,
            "book_id"  : self.book_id,
            "transaction_status" : self.transaction_status,
            "lender_id" : self.lender_id,
            "store_id" : self.store_id,
            "borrower_id" : self.borrower_id, 
            "lender_transaction_status" : self.lender_transaction_status,
            "store_transaction_status" : self.store_transaction_status,
            "borrower_transaction_status" : self.borrower_transaction_status,
            "book_price" : self.book_price,
            "transaction_upload_ts" : self.transaction_upload_ts,
            "transaction_submit_ts" : self.transaction_submit_ts,
            "transaction_pickup_ts" : self.transaction_pickup_ts,
            "transaction_return_ts" : self.transaction_return_ts,
            "transaction_lenderpickup_ts" : self.transaction_lenderpickup_ts,

        }

    def insert(self):
        db.session.add(self)
        db.session.commit()



    def delete(self):
        db.session.delete(self)
        db.session.commit()



    def update(self):
        db.session.commit()