import os
from flask import Flask, request, abort, jsonify ,make_response
from flask_cors import CORS
from models import setup_db, userModel, db_drop_and_create_all 
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import uuid
from  werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta,date



'''
commment after run 

db_drop_and_create_all()
'''

def create_app():
    app = Flask(__name__)

    


    setup_db(app)

    CORS(app)

    def token_required(f):
        @wraps(f)

        def decorated(*args, **kwargs):

            token = None
            if 'x-access-token' in request.headers:
                token = request.headers['x-access-token']
            if not token:
                return make_response('Could not verify',409,{'WWW-Authenticate' : 'token not found'})

            try:
                data = jwt.decode(token,app.config['SECRET_KEY'],algorithms=["HS256"])
                current_user = userModel.query.filter_by(usernumber = data['usernumber']).first()
                
            except:
                return make_response('Could not verify',409,{'WWW-Authenticate' : 'token not found'})

        
            return f(current_user,*args,**kwargs)
        
        return decorated


    @app.route('/User', methods=['POST'])
    @token_required
    def return_response(current_user):
        return jsonify(
                usernumber = current_user.usernumber,
                username  = current_user.username,
                email = current_user.email,
                firstname = current_user.firstname,
                lastname = current_user.lastname,
                dob = current_user.dob,
                phonenumber = current_user.phonenumber
            )

    @app.route('/Tokencheck', methods=['POST'])
    @token_required
    def check_token(current_user):
        return jsonify({'response' : 'false'})


    @app.route('/login', methods=['POST'])
    def login():
        auth = request.get_json()

        if not auth or not auth.get('username') or not auth.get('password'):
            return make_response(
                'Could not verify',
                401,
                {'WWW-Authenticate' : 'Login required'}
            )

        user = userModel.query.filter_by(username = auth.get('username')).first()

        if not user:
            return make_response(
                'Could not verify',
                401,
                {'WWW-Authenticate' : 'User does not exist'}
            )

        if check_password_hash(user.password, auth.get('password')):
            token = jwt.encode({
                'usernumber': user.usernumber,
                'exp': datetime.utcnow() + timedelta(minutes = 69)
            },app.config['SECRET_KEY'],algorithm="HS256")

            return make_response(jsonify(token = token,username = user.username,usernumber = user.usernumber),201)

        return make_response(
            'Could not verify',
            403,
            {'WWW-Authenticate' : 'Incorrect password'}
        )


    @app.route('/signup', methods=['POST'])
    def signup():
        data = request.get_json()

        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        firstname = data.get('firstname')
        lastname = data.get('lastname')
        year = data.get('year')
        month = data.get('month')
        day = data.get('day')
        phonenumber = data.get('phonenumber')

        
        try:
            dob = date(int(year),int(month),int(day))
        except:
            return make_response(
                'Invalid Date',
                201,
                {'WWW-Authenticate' : 'Invalid Date'}
            )

        
        user_username = userModel.query.filter_by(username = username).first()
        user_email = userModel.query.filter_by(email = email).first()

        if not user_username and not user_email:

            user = userModel(
                username = username,
                password = generate_password_hash(password),
                email = email,
                firstname = firstname,
                lastname = lastname,
                dob = dob,
                phonenumber = phonenumber
            )

            db.session.add(user)
            db.session.commit()

            return make_response(
                'Registration successful',
                201,
                {'WWW-Authenticate' : 'Registration successful'}
            )


        else:
            return make_response(
                'User already exists',
                201,
                {'WWW-Authenticate' : 'User already exists'}
            )



    @app.route('/changepassword',methods=['POST'])
    @token_required
    def changepassword(current_user):
        data = request.get_json()

        oldpassword = data.get('oldpassword')
        newpassword = data.get('newpassword')

        if check_password_hash(current_user.password, oldpassword):
            current_user.password  = generate_password_hash(newpassword)
            db.session.commit()
            return make_response(
                'Password changed!',
                602,
                {'WWW-Changepassword' : 'Password Changed!'}
            )
        else:
            return make_response(
                'Old password incorrect!',
                603,
                {'WWW-Changepassword' : 'Old password incorrect!'}
            )
        




    @app.route('/',methods=['GET'])
    def hello():
        return jsonify({'message': 'Hello,hello, World!'})



    return app



app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host='127.0.0.1',port=port,debug = True)