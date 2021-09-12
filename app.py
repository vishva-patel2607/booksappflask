import os
from flask import Flask,render_template, request, abort, jsonify ,make_response
from flask_cors import CORS
from models import setup_db, userModel,bookModel, db_drop_and_create_all 
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import uuid
from  werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta,date
from s3_functions import upload_file
from werkzeug.utils import secure_filename
import boto3





temp = [{"hello" : "how are you"},{"hello2" : "how are ypo2"}]

BUCKET = "booksapp-image-data"
BOOK_UPLOAD_FOLDER = "uploads"
BUCKET_LINK = "https://"+BUCKET+".s3.amazonaws.com/"

def create_app():
    app = Flask(__name__)

    


    setup_db(app)

    CORS(app)

    '''
    commment after run 
    db_drop_and_create_all()
    '''

    def token_required(f):
        @wraps(f)

        def decorated(*args, **kwargs):

            token = None
            if 'x-access-token' in request.headers:
                token = request.headers['x-access-token']
            if not token:
                return make_response( 
                    jsonify(
                        {
                            "message" : "Could not verify",
                            "status" : False,
                        }
                    ),
                    401
                )

            try:
                data = jwt.decode(token,app.config['SECRET_KEY'],algorithms=["HS256"])
                current_user = userModel.query.filter_by(usernumber = data['usernumber']).first()
                
            except:
                return make_response( 
                    jsonify(
                        {
                            "message" : "Could not verify",
                            "status" : False,
                        }
                    ),
                    401
                )

        
            return f(current_user,*args,**kwargs)
        
        return decorated


    @app.route('/User', methods=['POST'])
    @token_required
    def return_response(current_user):
        return make_response(
            jsonify(
                {
                    "status" : True,
                    "message" : "The user information succesfully accessed",
                    "response" : { 
                                    "user" : current_user.details()
                                }

                },
                200
            )
        )



    @app.route('/User/Login', methods=['POST'])
    def login():
        auth = request.get_json()

        if not auth or not auth.get('username') or not auth.get('password'):
            return make_response( 
                    jsonify(
                        {
                            "message" : "Login required",
                            "status" : False,
                        }
                    ),
                    401,
                    {'WWW-Authenticate' : 'Login required'}
                )

        user = userModel.query.filter_by(username = auth.get('username')).first()

        if not user:
            return make_response( 
                    jsonify(
                        {
                            "message" : "User does not exist",
                            "status" : False,
                        }
                    ),
                    401,
                    {'WWW-Authenticate' : 'User does not exist'}
                )

        if check_password_hash(user.password, auth.get('password')):
            token = jwt.encode({
                'usernumber': user.usernumber,
                'exp': datetime.utcnow() + timedelta(minutes = 69)
            },app.config['SECRET_KEY'],algorithm="HS256")

            return make_response(
                    jsonify(
                        {
                            "message" : "Log In successfull",
                            "status" : True,
                            "response" : {

                                            "token" : token,
                                            "username" : user.username,
                                            "usernumber" : user.usernumber
                                        }
                        }
                    ),
                    201
                )

        return make_response( 
                    jsonify(
                        {
                            "message" : "Incorrect password",
                            "status" : False,
                        }
                    ),
                    401,
                    {'WWW-Authenticate' : 'Incorrect password'}
                )


    @app.route('/User/Signup', methods=['POST'])
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
                    jsonify(
                        {
                            "message" : "Invalid Date",
                            "status" : False,
                        }
                    ),
                    400
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

            user.insert()

            return make_response(
                jsonify(
                        {
                            "message" : "Registration successful",
                            "status" : True,
                        }
                    ),
                201,
                {'WWW-Authenticate' : 'Registration successful'}
            )


        else:
            return make_response(
                jsonify(
                        {
                            "message" : "User already exists",
                            "status" : False,
                        }
                    ),
                400,
                {'WWW-Authenticate' : 'User already exists'}
            )



    @app.route('/User/Changepassword',methods=['PUT'])
    @token_required
    def changepassword(current_user):
        data = request.get_json()

        oldpassword = data.get('oldpassword')
        newpassword = data.get('newpassword')

        if check_password_hash(current_user.password, oldpassword):
            current_user.password  = generate_password_hash(newpassword)
            
            current_user.update()

            return make_response(
                jsonify(
                        {
                            "message" : "Password Changed",
                            "status" : True,
                        }
                    ),
                201,
                {'WWW-Authenticate' : 'Password Changed!'}
            )
        else:
            return make_response(
                jsonify(
                        {
                            "message" : 'Old password incorrect!',
                            "status" : False,
                        }
                    ),
                401,
                {'WWW-Authenticate' :  'Old password incorrect!'}
            )


    @app.route('/User/Changenumber',methods=['PUT'])
    @token_required
    def changephonenumber(current_user):
        data = request.get_json()

        newnumber = data.get('newnumber')

        current_user.phonenumber  = newnumber
            
        current_user.update()

        return make_response(
                jsonify(
                        {
                            "message" : "Phonenumber Changed",
                            "status" : True,
                        }
                    ),
                201
            )



    @app.route('/Book/upload',methods=['POST'])
    @token_required
    def uploadbook(current_user):
        book_name = request.form.get("book_name")
        book_year = request.form.get("book_year")
        book_condition = request.form.get("book_condition")
        book_img = request.files.get('book_img')
        book_price = request.form.get('book_price')
        store_id = request.form.get('store_id')
        usernumber = current_user.usernumber
        book_author = request.form.get('book_author')

        filename = secure_filename("book-"+datetime.utcnow().strftime("%m-%d-%Y_%H:%M:%S")+".jpg")
        upload_file(filename,BUCKET,body=book_img)
        
        book_img_url = BUCKET_LINK+"filename"

        book = bookModel(
            book_name  = book_name,
            book_year = book_year,
            book_condition = book_condition,
            book_img = book_img_url,
            book_price = book_price,
            store_id = store_id,
            usernumber = usernumber,
            book_author = book_author
        )

        book.insert()

        return make_response(
            jsonify(
                {
                            "message" : "Phonenumber Changed",
                            "status" : True,
                            "response" : book.details()
                }
            ),
            201
        )



    @app.route('/Book/uploadedbooks',methods=['POST'])
    @token_required
    def uploadedbooks(current_user):

        books = bookModel.query.filter_by(usernumber = current_user.usernumber).all()

        booklist = [book.details() for book in books]

        return make_response(
            jsonify(
                {
                            "message" : "Phonenumber Changed",
                            "status" : True,
                            "response" : {
                                "books" : booklist
                            }
                }
            ),
            200
        )




    

        




    @app.route('/',methods=['GET'])
    def hello():
        return jsonify({"hello": temp})



    return app



app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host='127.0.0.1',port=port,debug = True)