from crypt import methods
from email import message
import json
from multiprocessing import connection
import os
from flask import Flask,render_template, request, abort, jsonify ,make_response, session, redirect

from flask.helpers import url_for
from flask_cors import CORS
from sqlalchemy.sql.expression import true
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.sql.type_api import NULLTYPE
from models import booksubjectsModel, invoiceModel, setup_db, storeModel, transactionModel, userModel,bookModel, db_drop_and_create_all , db, userpntokenModel

from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import uuid
from  werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta,date
from s3_functions import upload_file,remove_file
from werkzeug.utils import secure_filename
import boto3
from status import invoice_statuses, transaction_statuses,lender_transaction_statuses,store_transaction_statuses,borrower_transaction_statuses, Usertype, Transactiontype
from geoalchemy2.types import Geometry
from geoalchemy2.comparator import Comparator
import geoalchemy2.functions as func
from jinja2 import TemplateNotFound
from notification import subscribetonotification,sendsmsmessage
from config import configure_app
from utility import booksubjectAdd, generateBill,generateOTP, getpricing


from mail import sendverifymail,sendchangepasswordmail
from rq import Queue,Retry
from redisconnection import conn








def create_app():
    app = Flask(__name__)

    

    setup_db(app)
    configure_app(app)
    
    mail_queue = Queue('mail',connection=conn)
    notification_queue = Queue('notification',connection=conn)
    utility_queue = Queue('notification',connection=conn)
    
    
    
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

    def token_required_store(f):
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
                current_user = userModel.query.filter(userModel.usernumber == data['usernumber']).filter(userModel.usertype == Usertype.store.name).first()
                assert(current_user is not None)
                current_store = storeModel.query.filter(storeModel.usernumber == current_user.usernumber).first()
                assert(current_store is not None)
                
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

        
            return f(current_user,current_store,*args,**kwargs)
        
        return decorated


    def token_required_admin(f):
        @wraps(f)

        def decorated(*args, **kwargs):

            token = None
            if 'x-access-token' in session:
                token = session['x-access-token']
            if not token:
                return render_template('login.html',error = "Token missing login again 1")

            try:
                data = jwt.decode(token,app.config['SECRET_KEY'],algorithms=["HS256"])
                current_user = userModel.query.filter_by(usernumber = data['usernumber']).first()
                
            except:
                return render_template('login.html',error = "Token missing login again 2")

        
            return f(current_user,*args,**kwargs)
        
        return decorated
        
    @app.route('/Notification/Subscribe',methods=['POST'])
    @token_required
    def usersubscribetonotification(current_user):
        data = request.get_json()

        usernumber = current_user.usernumber
        devicepushtoken = data.get('devicepushtoken')
        platform = data.get('platform')

        token = userpntokenModel.query.\
                filter(userpntokenModel.usernumber == usernumber).\
                filter(userpntokenModel.devicetoken == devicepushtoken).\
                first()
        
        if token is not None :
            return make_response(
                jsonify(
                    {
                        "status" : False,
                        "message" : "Device is alredy registered with this usernumber",
                    },
                ),
                200
            )
        else :
            if platform == 'android':
                platformarn = app.config['FCM_ARN']
                notification_queue.enqueue(subscribetonotification,app.config['AWS_ACCESS_KEY_ID'],app.config['AWS_SECRET_ACCESS_KEY'],platformarn,usernumber,devicepushtoken,platform)

                return make_response(
                    jsonify(
                        {
                            "status" : True,
                            "message" : "Device registered with this usernumber",
                        },
                    ),
                    200
                )

            return make_response(
                    jsonify(
                        {
                            "status" : False,
                            "message" : "Device not registered",
                        },
                    ),
                    200
                )

    @app.route('/User/Verify/Phonenumber/<usernumber>/<phonenumber>',methods=['GET','POST'])
    def testingmessaging(usernumber=None,phonenumber=None):
        usernumber = usernumber
        phonenumber = phonenumber
        user = userModel.query.filter(userModel.usernumber == usernumber).first()

        if usernumber is not None and phonenumber is not None and user is not None: #and user.phn_verified is not None and user.phn_verified != False:
            if request.method == 'GET':
                otp = generateOTP()

                conn.set(
                        usernumber,
                        json.dumps({
                                'usernumber': usernumber,
                                'phonenumber': phonenumber,
                                'OTP' : otp
                            }),
                        ex=600
                        )
                message = str('The OTP for verifying your Booksapp account mobile number is : '+otp)
                sendsmsmessage(app.config['AWS_ACCESS_KEY_ID'],app.config['AWS_SECRET_ACCESS_KEY'],phonenumber,message)
                return make_response(
                                jsonify(
                                    {
                                        "status" : True,
                                        "message" : "Message with OTP sent!"
                                    },
                                ),
                                200
                            )
            else:
                data = request.get_json()
                request_otp = data.get('otp')
                byte_value= conn.get(usernumber)
                
                if byte_value is None:
                    return make_response(
                                jsonify(
                                    {
                                        "status" : False,
                                        "message" : "Could not verify!"
                                    },
                                ),
                                400
                            )
                else:
                    value = json.loads(byte_value.decode('utf-8'))
                    if value['OTP'] == request_otp and phonenumber == value['phonenumber']:
                        conn.delete(usernumber)
                        user.phonenumber = value['phonenumber']
                        user.phn_verified = True
                        user.phn_verified_on = datetime.utcnow()
                        user.update()

                        return make_response(
                                jsonify(
                                    {
                                        "status" : True,
                                        "message" : "User phone number verified"
                                    },
                                ),
                                201
                            )
                    else :
                        return make_response(
                                jsonify(
                                    {
                                        "status" : False,
                                        "message" : "OTP did not match"
                                    },
                                ),
                                400
                            )
        else:
            return make_response(
                                jsonify(
                                    {
                                        "status" : False,
                                        "message" : "Cannot verify this user!"
                                    },
                                ),
                                404
                            )



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
            ),
            200
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


        if not user or user.usertype != Usertype.user.name:
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
            emailverified = True
            phoneverified = True
            if not user.email_verified or user.email_verified is None:
                emailverified = False
                token = jwt.encode({
                    'usernumber': user.usernumber,
                    'exp': datetime.utcnow() + timedelta(minutes = 30)
                },app.config['SECRET_KEY'],algorithm="HS256")

                url = url_for('verifyuser',token = token,_external=True)
                template = render_template('verifyTokenEmail.html',url = url)
                mail_queue.enqueue(sendverifymail,app.config['AWS_ACCESS_KEY_ID'],app.config['AWS_SECRET_ACCESS_KEY'],app.config['MAILER_ADDRESS'],user.email,template,retry=Retry(max=2))
                
            if not user.phn_verified or user.phn_verified is None:
                phoneverified = False
                return make_response(
                        jsonify(
                            {
                                "message" : "User is not verified",
                                "status" : False,
                                "response" : {

                                            "emailverified" : emailverified,
                                            "phoneverified" : phoneverified
                                        }
                            }
                        ),
                        402
                    )
                
            token = jwt.encode({
                'usernumber': user.usernumber,
                'exp': datetime.utcnow() + timedelta(minutes = 1000)
            },app.config['SECRET_KEY'],algorithm="HS256")

            return make_response(
                    jsonify(
                        {
                            "message" : "Log In successfull",
                            "status" : True,
                            "response" : {

                                            "token" : token,
                                            "username" : user.username,
                                            "usernumber" : user.usernumber,
                                            "emailverified" : emailverified,
                                            "phoneverified" : phoneverified
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

    @app.route('/User/Signup/<string:username>/<string:email>',methods=['GET'])
    @app.route('/User/Signup', methods=['POST'])
    def signup(username=None,email=None):
        if request.method == 'POST':
            data = request.get_json()

            username = data.get('username').lower()
            password = data.get('password')
            email = data.get('email').lower()
            firstname = data.get('firstname').lower()
            lastname = data.get('lastname').lower()
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

            
            user_test = userModel.query.filter((userModel.username == username) | (userModel.email == email)).first()

            if user_test is None:

                user = userModel(
                    username = username,
                    password = generate_password_hash(password),
                    email = email,
                    firstname = firstname,
                    lastname = lastname,
                    dob = dob,
                    phonenumber = phonenumber,
                    created_on=datetime.utcnow(),
                    usertype = Usertype.user.name
                )

                user.insert()
                token = jwt.encode({
                    'usernumber': user.usernumber,
                    'exp': datetime.utcnow() + timedelta(minutes = 30)
                },app.config['SECRET_KEY'],algorithm="HS256")

                url = url_for('verifyuser',token = token,_external=True)
                template = render_template('verifyTokenEmail.html',url = url)
                mail_queue.enqueue(sendverifymail,app.config['AWS_ACCESS_KEY_ID'],app.config['AWS_SECRET_ACCESS_KEY'],app.config['MAILER_ADDRESS'],user.email,template,retry=Retry(max=2))

                return make_response(
                    jsonify(
                            {
                                "message" : "Registration successful",
                                "status" : True,
                                "response" : {
                                        "user" : user.details()
                                }
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
                                "response" : {

                                                "user" : user_test.details()
                                            }                                                   #please delete once otp feature is done!
                            }
                        ),
                    400,
                    {'WWW-Authenticate' : 'User already exists'}
                )
        else:
            if username is None or email is None:
                return make_response(
                    jsonify(
                            {
                                "message" : "Please provide both the information",
                                "status" : False,
                            }
                        ),
                    400,
                    {'WWW-Authenticate' : 'Provide proper information'}
                )
            else:
                user_check = userModel.query.filter((userModel.username == username.lower()) | (userModel.email == email.lower())).first()

                if user_check is None:
                    return make_response(
                        jsonify(
                                {
                                    "message" : "User can be created",
                                    "status" : True,
                                }
                            ),
                        200
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


    @app.route('/User/Verify/User/<token>',methods = ['GET'])
    def verifyuser(token):
        try:
            data = jwt.decode(token,app.config['SECRET_KEY'],algorithms=["HS256"])
            user = userModel.query.filter_by(usernumber = data['usernumber']).first()
            user.email_verified = True
            user.verified_on = datetime.utcnow()
            if user.created_on == None:
                user.verified_on = datetime.utcnow()
            user.update()
            return render_template('verifiedTokenEmail.html',msg = "The Account has been verified!")
        except:
            return render_template('verifiedTokenEmail.html',msg='Account could not be verified by this link try to login again with your account in the app to get a new link!')

    
    
    
    @app.route('/User/Verify/Changepassword/<token>',methods = ['GET'])
    def verifychangepassword(token):
        try:
            data = jwt.decode(token,app.config['SECRET_KEY'],algorithms=["HS256"])
            url = url_for('resetpassword',token = token,_external=True)
            return render_template('verifiedTokenPassword.html',url = url)
        except:
            return render_template('notverifiedTokenPassword.html')


    
    
    
    @app.route('/User/Changeemail',methods=['POST'])
    @token_required
    def changeemail(current_user):

        data = request.get_json()
        newemail = data.get('email')

        current_user.email = newemail
        current_user.update()

        token = jwt.encode({
                    'usernumber': current_user.usernumber,
                    'exp': datetime.utcnow() + timedelta(minutes = 30)
                },app.config['SECRET_KEY'],algorithm="HS256")

        url = url_for('verifyuser',token = token,_external=True)
        template = render_template('verifyTokenEmail.html',url = url)
        mail_queue.enqueue(sendverifymail,app.config['AWS_ACCESS_KEY_ID'],app.config['AWS_SECRET_ACCESS_KEY'],app.config['MAILER_ADDRESS'],current_user.email,template,retry=Retry(max=2))


        return make_response( 
                    jsonify(
                        {
                            "message" : "Email Changed and a verification mail is sent",
                            "status" : True,
                        }
                    ),
                    201
                )



    @app.route('/User/Forgotpassword',methods=['POST'])
    def forgotpassword():
        data = request.get_json()

        username = data.get('username')

        user = userModel.query.filter_by(username = username).first()
        
        if not user:
            return make_response(
                jsonify(
                        {
                            "message" : "Username does not exist!",
                            "status" : False,
                        }
                    ),
                400,
            )
        
        else: 
            if not user.email_verified or user.email_verified == None:
                return make_response(
                    jsonify(
                            {
                                "message" : "User not verified",
                                "status" : False,
                            }
                        ),
                    400,
                )
            
            else: 
            
                store = storeModel.query.filter_by(usernumber = user.usernumber).first()

                if store:
                    return make_response(
                        jsonify(
                                {
                                    "message" : "Accounts linked to stores cannot be used in the app",
                                    "status" : False,
                                }
                            ),
                        400,
                    )
                
                else:
                    
                    token = jwt.encode({
                        'usernumber': user.usernumber,
                        'exp': datetime.utcnow() + timedelta(minutes = 30)
                    },app.config['SECRET_KEY'],algorithm="HS256")

                    url = url_for('verifychangepassword',token = token,_external=True)
                    template = render_template('verifyTokenPassword.html',url = url)
                    mail_queue.enqueue(sendchangepasswordmail,app.config['AWS_ACCESS_KEY_ID'],app.config['AWS_SECRET_ACCESS_KEY'],app.config['MAILER_ADDRESS'],user.email,template,retry=Retry(max=2))

                    return make_response(
                            jsonify(
                                    {
                                        "message" : "A link to change your password is sent to your registered email address",
                                        "status" : True,
                                    }
                                ),
                            201,
                            {'WWW-Authenticate' : 'Registration successful'}
                        )

        
      
    @app.route('/User/Resetpassword/<token>',methods=['POST'])
    def resetpassword(token):
        try:
            data = jwt.decode(token,app.config['SECRET_KEY'],algorithms=["HS256"])
            newpassword = request.form.get('password')

            user = userModel.query.filter_by(usernumber = data['usernumber']).first()

            user.password = generate_password_hash(newpassword)
            user.update()
            return render_template('verifiedTokenEmail.html',msg = "The password has been updated")
        except:
            return render_template('verifiedTokenEmail.html',msg = "The password could not be changed")



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

    @app.route('/Book/Search/<int:offset>', methods = ['POST'])
    @token_required
    def searchbooks(current_user,offset=1,limit=10):

        data = request.get_json()

        book_query = data.get("book_query")
        longitude = data.get("longitude")
        latitude = data.get("latitude")
        distance_filter =  data.get("distance_filter")
        price_filter = data.get("price_filter")
        genre_filter = data.get("genre_filter")

        query_string = "%"+book_query+"%"

        keyword_search = booksubjectsModel.query.filter(booksubjectsModel.book_subject.ilike(query_string)).all()
        bookids = [subjects.book_id for subjects in keyword_search]

        result = db.session.query(bookModel,transactionModel,storeModel).\
                            filter(bookModel.usernumber != current_user.usernumber).\
                            filter((transactionModel.transaction_status == transaction_statuses.lend.submitted_by_lender) | (transactionModel.transaction_status == transaction_statuses.sell.submitted_by_seller) ).\
                            filter(bookModel.store_id == storeModel.store_id).\
                            filter(bookModel.book_id == transactionModel.book_id).\
                            filter(bookModel.book_name.ilike(query_string) | (bookModel.book_id.in_(bookids)))
                            
        if price_filter == 1:
            result = result.filter(bookModel.book_price <= 250)
        elif price_filter == 2:
            result = result.filter(bookModel.book_price >= 250).filter(bookModel.book_price <= 500)
        elif price_filter == 3:
            result = result.filter(bookModel.book_price >= 500).filter(bookModel.book_price <= 750)
        elif price_filter == 4:
            result = result.filter(bookModel.book_price >= 750)

        if genre_filter and genre_filter is not None:
            result =  result.filter(bookModel.book_category.in_(genre_filter))
        
        if distance_filter is not None and distance_filter == 1:
            result = result.order_by(Comparator.distance_centroid(storeModel.store_location,func.ST_GeographyFromText('SRID=4326;POINT(%.8f %.8f)' % (longitude,latitude))))
        elif distance_filter is not None and distance_filter == 2:
            result = result.order_by(Comparator.distance_centroid(storeModel.store_location,func.ST_GeographyFromText('SRID=4326;POINT(%.8f %.8f)' % (longitude,latitude))).desc())
        else:
            result = result.order_by(Comparator.distance_centroid(storeModel.store_location,func.ST_GeographyFromText('SRID=4326;POINT(%.8f %.8f)' % (longitude,latitude))))
        
        if offset is not None:
            result = result.offset((offset-1)*limit).limit(limit).all()
        else:
            result = result.limit(limit).all()

        retlist = []
        for book,transaction,store in result:
            book_dict = book.details()
            book_dict['store_distance'] = store.getdistance(longitude,latitude)
            book_dict['transaction_type'] = transaction.transaction_type
            book_dict['store'] = store.details()
            book_dict
            retlist.append(book_dict)

       

        return make_response(
                jsonify(
                {
                            "message" : "All the Books for given query",
                            "status" : True,
                            "response" : {
                                "book_list" : retlist,
                            }
                }
                ),
                201
        )
            


    @app.route('/Book/Upload/Image',methods=['POST','PUT','GET','DELETE'])
    @token_required
    def uploadbookimage(current_user):

        redis_key = "image_upload_"+str(current_user.usernumber)
        if request.method == 'POST':
            book_img = request.files['book_img']
            filename = secure_filename("book-"+datetime.utcnow().strftime("%m-%d-%Y_%H:%M:%S")+".jpg")
            response = upload_file(app.config['AWS_ACCESS_KEY_ID'],app.config['AWS_SECRET_ACCESS_KEY'],filename,app.config['BUCKET'],body=book_img)
            book_img_url = app.config['IMAGE_BUCKET_LINK']+filename
            conn.set(redis_key,book_img_url)
            return make_response(
                jsonify(
                    {
                                "message" : "Image uploaded",
                                "status" : True,
                                "response" : {
                                    "book" : book_img_url
                                }
                    }
                ),
                201
            )

        elif request.method == "PUT":
            old_book_url = request.form.get("old_book_img_url")
            old_book_filename = old_book_url.replace(app.config['IMAGE_BUCKET_LINK'],"")
            remove_response = remove_file(app.config['AWS_ACCESS_KEY_ID'],app.config['AWS_SECRET_ACCESS_KEY'],old_book_filename,app.config['BUCKET'])
            book_img = request.files['book_img']
            filename = secure_filename("book-"+datetime.utcnow().strftime("%m-%d-%Y_%H:%M:%S")+".jpg")
            upload_response = upload_file(app.config['AWS_ACCESS_KEY_ID'],app.config['AWS_SECRET_ACCESS_KEY'],filename,app.config['BUCKET'],body=book_img)
            book_img_url = app.config['IMAGE_BUCKET_LINK']+filename
            conn.set(redis_key,book_img_url)
            return make_response(
                jsonify(
                    {
                                "message" : "Image changed succesfully",
                                "status" : True,
                                "response" : {
                                    "book" : book_img_url
                                }
                    }
                ),
                201
            )
        elif request.method == "DELETE":
            old_book_url = request.form.get("old_book_img_url")
            old_book_filename = old_book_url.replace(app.config['IMAGE_BUCKET_LINK'],"")
            remove_response = remove_file(app.config['AWS_ACCESS_KEY_ID'],app.config['AWS_SECRET_ACCESS_KEY'],old_book_filename,app.config['BUCKET'])
            conn.delete(redis_key)
            return make_response(
                jsonify(
                    {
                                "message" : "Image removed succesfully",
                                "status" : True
                    }
                ),
                201
            )
        
        else : 
                url = conn.get(redis_key)
                
                if url is None:
                    return make_response(
                                jsonify(
                                    {
                                        "status" : False,
                                        "message" : "No cached image!"
                                    },
                                ),
                                200
                            )
                else:
                    url = url.decode("utf-8")
                    return make_response(
                            jsonify(
                                {
                                    "status" : True,
                                    "message" : "Cached image url",
                                    "url" : url
                                },
                            ),
                            201
                        )

            

    @app.route('/Book/Upload/Getpricing/<string:transaction_type>/<int:book_price>',methods = ['GET'])
    @token_required
    def getuploadbookpricing(current_user,transaction_type = None,book_price = None):
        if transaction_type is not None and book_price is not None:
            pricing = getpricing(transaction_type=transaction_type,book_price=book_price)
            return make_response(
                jsonify(
                    {
                                "message" : "Book Pricing",
                                "status" : True,
                                "response" : {
                                    "pricing" : pricing,
                                }
                    }
                ),
                200
            )
        else:
            return make_response(
                jsonify(
                     {
                                "message" : "Can't retrieve pricing",
                                "status" : False,
                    }
                ),
                404
            )

    @app.route('/Book/Upload',methods=['POST'])
    @token_required
    def uploadbook(current_user):
        book_name = request.form.get("book_name").lower()
        book_year = request.form.get("book_year")
        book_condition = request.form.get("book_condition").lower()
        book_img_url = request.form.get('book_img_url')
        book_price = int(request.form.get('book_price'))
        store_id = request.form.get('store_id')
        usernumber = current_user.usernumber
        book_author = request.form.get('book_author').lower()
        book_category = request.form.get('book_category').lower()
        book_isbn = request.form.get('book_isbn')


        if request.form.get('transaction_type').lower() == Transactiontype.lend.name:
            book = bookModel(
                book_name  = book_name,
                book_year = book_year,
                book_condition = book_condition,
                book_img = book_img_url,
                book_price = book_price,
                store_id = store_id,
                usernumber = usernumber,
                book_author = book_author,
                book_isbn= book_isbn,
                book_category=book_category
            )

            book.insert()

            transaction = transactionModel(
                book_id= book.book_id,
                transaction_status= transaction_statuses.lend.uploaded_with_lender,
                lender_id= usernumber,
                store_id= store_id,
                borrower_id= None,
                invoice_id = None,
                lender_transaction_status= lender_transaction_statuses.lend.pending,
                store_transaction_status= store_transaction_statuses.lend.pending,
                borrower_transaction_status = borrower_transaction_statuses.lend.pending,
                book_price= book_price,
                transaction_upload_ts= datetime.now(),
                transaction_submit_ts= None,
                transaction_pickup_ts= None,
                transaction_return_ts= None,
                transaction_lenderpickup_ts= None,
                transaction_type=Transactiontype.lend.name
            )

            transaction.insert()
        else :

            book = bookModel(
                book_name  = book_name,
                book_year = book_year,
                book_condition = book_condition,
                book_img = book_img_url,
                book_price = book_price,
                store_id = store_id,
                usernumber = usernumber,
                book_author = book_author,
                book_isbn= book_isbn,
                book_category=book_category
            )

            book.insert()

            transaction = transactionModel(
                book_id= book.book_id,
                transaction_status= transaction_statuses.sell.uploaded_with_seller,
                lender_id= usernumber,
                store_id= store_id,
                borrower_id= None,
                invoice_id = None,
                lender_transaction_status= lender_transaction_statuses.sell.pending,
                store_transaction_status= store_transaction_statuses.sell.pending,
                borrower_transaction_status = borrower_transaction_statuses.sell.pending,
                book_price= book_price,
                transaction_upload_ts= datetime.now(),
                transaction_submit_ts= None,
                transaction_pickup_ts= None,
                transaction_return_ts= None,
                transaction_lenderpickup_ts= None,
                transaction_type=Transactiontype.sell.name
            )

            transaction.insert()

        
        redis_key = "image_upload_"+str(current_user.usernumber)
        conn.delete(redis_key)
        


        utility_queue.enqueue(booksubjectAdd,book.book_id,book.book_isbn)

        


        return make_response(
            jsonify(
                {
                            "message" : "Book uploaded",
                            "status" : True,
                            "response" : {
                                "book" : book.details(),
                                "transaction" : transaction.details(),
                            }
                }
            ),
            201
        )


    ######################################### HOME PAGE ################################################


    ##################################################################################
    # TO GET ALL THE BOOKS THAT USER HAS LENT CURRENTLY
    ##################################################################################
    @app.route('/Book/Uploadedbooks',methods=['POST'])              #delete once done
    @app.route('/Book/Lent', methods=['GET'])
    @token_required
    def lentbooks(current_user):

        booklist = [] 

        result =  db.session.query(bookModel,transactionModel,storeModel).\
                    filter(bookModel.usernumber == current_user.usernumber).\
                    filter(bookModel.book_id == transactionModel.book_id).\
                    filter(bookModel.store_id == storeModel.store_id).\
                    filter(transactionModel.transaction_type == Transactiontype.lend.name).\
                    filter(transactionModel.transaction_status != transaction_statuses.lend.pickup_by_lender).\
                    all()

        if not result or result is not None:
            for book,transaction,store in result:
                book_dict = book.details()
                book_dict['book_transaction_type'] = transaction.transaction_type
                book_dict['book_transaction_status'] = transaction.transaction_status
                book_dict['book_transaction_code'] = transaction.getcodes()
                book_dict['store'] = store.details()
                booklist.append(book_dict)

            

            return make_response(
                jsonify(
                    {
                                "message" : "All the books for the user retrieved",
                                "status" : True,
                                "response" : {
                                    "books" : booklist
                                }
                    }
                ),
                200
            )
        else:
            return make_response(
                jsonify(
                    {
                                "message" : "No books lent yet",
                                "status" : False,
                    }
                ),
                200
            )

    ##################################################################################
    # TO GET ALL THE BOOKS THAT USER HAS SOLD CURRENTLY
    ##################################################################################
    @app.route('/Book/Sold', methods=['GET'])
    @token_required
    def soldbooks(current_user):

        booklist = [] 

        result =  db.session.query(bookModel,transactionModel,storeModel).\
                    filter(bookModel.usernumber == current_user.usernumber).\
                    filter(bookModel.book_id == transactionModel.book_id).\
                    filter(bookModel.store_id == storeModel.store_id).\
                    filter(transactionModel.transaction_type == Transactiontype.sell.name).\
                    filter(transactionModel.transaction_status != transaction_statuses.sell.collected_by_seller).\
                    filter(transactionModel.transaction_status != transaction_statuses.sell.pickup_by_seller).\
                    all()

        if not result or result is not None:
            for book,transaction,store in result:
                book_dict = book.details()
                book_dict['book_transaction_type'] = transaction.transaction_type
                book_dict['book_transaction_status'] = transaction.transaction_status
                book_dict['book_transaction_code'] = transaction.getcodes()
                book_dict['store'] = store.details()
                booklist.append(book_dict)

            

            return make_response(
                jsonify(
                    {
                                "message" : "All the books user has sold yet",
                                "status" : True,
                                "response" : {
                                    "books" : booklist
                                }
                    }
                ),
                200
            )
        else:
            return make_response(
                jsonify(
                    {
                                "message" : "No books sold yet",
                                "status" : False,
                    }
                ),
                200
            )
        


    @app.route('/Book/Lent/Edit',methods=['PUT'])
    @app.route('/Book/Borrowed/Edit',methods=['PUT'])
    @token_required
    def edituploadedbook(current_user):

        data = request.get_json()
        book_id = data.get('book_id')
        book_name = data.get('book_name')
        book_author = data.get('book_author')
        book_price = int(data.get('book_price'))
        book_condition = data.get('book_condition')
        book_year = data.get('book_year')
        book_transaction_type = data.get('book_transaction_type')


        data =  db.session.query(bookModel,transactionModel).\
                    filter(bookModel.book_id == book_id).\
                    filter(transactionModel.book_id == bookModel.book_id).\
                    filter(transactionModel.transaction_status.in_([transaction_statuses.lend.uploaded_with_lender,transaction_statuses.lend.submitted_by_lender,transaction_statuses.sell.uploaded_with_seller,transaction_statuses.sell.submitted_by_seller])).\
                    first()

        if data is not None: 
            book,transaction =  data 
            book.book_name = book_name
            book.book_author = book_author
            book.book_price = book_price
            book.book_condition = book_condition
            book.book_year = book_year
            transaction.transaction_type = book_transaction_type
            transaction.changeprice(book_price = book_price,transaction_type = book_transaction_type)
            book.update()
            transaction.update()

            return make_response(
                jsonify(
                    {
                                "message" : "Book Updated",
                                "status" : True,
                                "response" : {
                                    "book" : book.details(),
                                    "transaction" : transaction.details()
                                }
                    }
                ),
                201
            )
        else:
            return make_response(
                jsonify(
                    {
                                "message" : "This book can't be updated!",
                                "status" : False
                    }
                ),
                201
            )

    
            
            
    

    ##################################################################################
    # TO GET ALL THE BOOKS USER HAS BORROWED CURRENTLY
    ##################################################################################
    @app.route('/Book/Pickedupbooks',methods=['POST'])
    @app.route('/Book/Borrowed',methods=['GET'])
    @token_required
    def pickedupbooks(current_user):


        booklist = [] 

        result =  db.session.query(bookModel,transactionModel,storeModel).\
                    filter(transactionModel.borrower_id == current_user.usernumber).\
                    filter(transactionModel.book_id == bookModel.book_id).\
                    filter(bookModel.store_id == storeModel.store_id).\
                    filter(transactionModel.transaction_type == Transactiontype.lend.name).\
                    filter((transactionModel.transaction_status == transaction_statuses.lend.borrowed_by_borrower)|(transactionModel.transaction_status == transaction_statuses.lend.return_by_borrower)).\
                    all()
        if not result or result is not None:
            
            for book,transaction,store in result:
                book_dict = book.details()
                book_dict['book_transaction_type'] = transaction.transaction_type
                book_dict['book_transaction_status'] = transaction.transaction_status
                book_dict['book_transaction_code'] = transaction.getcodes()
                book_dict['book_pickup_date'] = transaction.transaction_pickup_ts.strftime("%m-%d-%Y")
                book_dict['store'] = store.details()
                booklist.append(book_dict)

        

            return make_response(
                jsonify(
                    {
                                "message" : "All the books for the user has Borrowed",
                                "status" : True,
                                "response" : {
                                    "books" : booklist
                                }
                    }
                ),
                200
            )
        else:
            return make_response(
                jsonify(
                    {
                                "message" : "No books borrowed yet",
                                "status" : False,
                    }
                ),
                200
            )


        

    ##################################################################################
    # TO GET ALL THE BOOKS USER HAS BOUGHT CURRENTLY
    ##################################################################################
    @app.route('/Book/Bought',methods=['GET'])
    @token_required
    def boughtbooks(current_user):


        booklist = [] 

        result =  db.session.query(bookModel,transactionModel,storeModel).\
                    filter(transactionModel.borrower_id == current_user.usernumber).\
                    filter(transactionModel.book_id == bookModel.book_id).\
                    filter(bookModel.store_id == storeModel.store_id).\
                    filter(transactionModel.transaction_type == Transactiontype.sell.name).\
                    filter(transactionModel.transaction_status == transaction_statuses.sell.booked_by_buyer).\
                    all()

        if not result or result is not None:
            for book,transaction,store in result:
                book_dict = book.details()
                book_dict['book_transaction_type'] = transaction.transaction_type
                book_dict['book_transaction_status'] = transaction.transaction_status
                book_dict['book_transaction_code'] = transaction.getcodes()
                book_dict['book_pickup_date'] = transaction.transaction_pickup_ts.strftime("%m-%d-%Y")
                book_dict['store'] = store.details()
                booklist.append(book_dict)

            

            return make_response(
                jsonify(
                    {
                                "message" : "All the books for the user has bought",
                                "status" : True,
                                "response" : {
                                    "books" : booklist
                                }
                    }
                ),
                200
            )
        else:
            return make_response(
                jsonify(
                    {
                                "message" : "No books bought yet",
                                "status" : False,
                    }
                ),
                200
            )
        

    ##################################################################################
    # TO GET ALL THE BOOK PICKUPS FOR THE USER
    ##################################################################################
    @app.route('/Book/Pickedupbooks/Added',methods=['POST'])
    @app.route('/Book/Pickups',methods=['GET'])
    @token_required
    def pickups(current_user):

        booklist = [] 

        result1 =  db.session.query(bookModel,transactionModel,storeModel).\
                    filter(transactionModel.borrower_id == current_user.usernumber).\
                    filter(transactionModel.book_id == bookModel.book_id).\
                    filter(bookModel.store_id == storeModel.store_id).\
                    filter(transactionModel.transaction_status.in_([transaction_statuses.lend.pickup_by_borrower,transaction_statuses.sell.booked_by_buyer])).\
                    all()

        result2 =  db.session.query(bookModel,transactionModel,storeModel).\
                    filter(transactionModel.lender_id == current_user.usernumber).\
                    filter(transactionModel.book_id == bookModel.book_id).\
                    filter(bookModel.store_id == storeModel.store_id).\
                    filter(transactionModel.transaction_status.in_([transaction_statuses.lend.submitted_by_borrower,transaction_statuses.lend.removed_by_lender,transaction_statuses.sell.pickup_by_buyer,transaction_statuses.sell.removed_by_seller])).\
                    all()
        
        if result1 or result2 or result1 is not None or result2 is not None:
            if not result1 or result1 is None:
                result = result2
            elif not result2 or result2 is None:
                result = result1
            else:
                result = result1+result2
            
            for book,transaction,store in result:
                book_dict = book.details()
                book_dict['book_transaction_code'] = transaction.getcodes()
                book_dict['book_transaction_type'] = transaction.transaction_type
                book_dict['book_transaction_status'] = transaction.transaction_status
                book_dict['store'] = store.details()
                booklist.append(book_dict)

            return make_response(
                jsonify(
                    {
                                "message" : "All the books for the user has added to pick up",
                                "status" : True,
                                "response" : {
                                    "books" : booklist
                                }
                    }
                ),
                200
            )
        else:
            return make_response(
                jsonify(
                    {
                                "message" : "No pickups currently",
                                "status" : False,
                    }
                ),
                200
            )


    ##################################################################################
    # TO GET ALL THE BOOK DROPOFFS FOR THE USER
    ##################################################################################
    @app.route('/Book/Pickedupbooks/Removed',methods=['POST'])
    @app.route('/Book/Dropoffs',methods=['GET'])
    @token_required
    def dropoffs(current_user):

        booklist = [] 

        result1 =  db.session.query(bookModel,transactionModel,storeModel).\
                    filter(transactionModel.lender_id == current_user.usernumber).\
                    filter(transactionModel.book_id == bookModel.book_id).\
                    filter(bookModel.store_id == storeModel.store_id).\
                    filter(transactionModel.transaction_status.in_([transaction_statuses.lend.uploaded_with_lender,transaction_statuses.sell.uploaded_with_seller])).\
                    all()

        result2 =  db.session.query(bookModel,transactionModel,storeModel).\
                    filter(transactionModel.borrower_id == current_user.usernumber).\
                    filter(transactionModel.book_id == bookModel.book_id).\
                    filter(bookModel.store_id == storeModel.store_id).\
                    filter(transactionModel.transaction_status == transaction_statuses.lend.return_by_borrower).\
                    all()

        if result1 or result2 or result1 is not None or result2 is not None:
            if not result1 or result1 is None:
                result = result2
            elif not result2 or result2 is None:
                result = result1
            else:
                result = result2+result1
        
            for book,transaction,store in result:
                book_dict = book.details()
                book_dict['book_transaction_code'] = transaction.getcodes()
                book_dict['book_transaction_type'] = transaction.transaction_type
                book_dict['book_transaction_status'] = transaction.transaction_status
                book_dict['store'] = store.details()
                booklist.append(book_dict)

            return make_response(
                jsonify(
                    {
                                "message" : "All the books for the user to drop off",
                                "status" : True,
                                "response" : {
                                    "books" : booklist
                                }
                    }
                ),
                200
            )
        else:
            return make_response(
                jsonify(
                    {
                                "message" : "No pickups currently",
                                "status" : False,
                    }
                ),
                200
            )




    ##################################################################################
    # TO GET ALL THE PREVIOUS TRANSACTION
    ##################################################################################
    @app.route('/Book/Previoustransactions',methods=['GET'])
    @token_required
    def previoustransactions(current_user):

        booklist = [] 

        result1 =  db.session.query(bookModel,transactionModel,storeModel).\
                    filter((transactionModel.borrower_id == current_user.usernumber)).\
                    filter(transactionModel.book_id == bookModel.book_id).\
                    filter(bookModel.store_id == storeModel.store_id).\
                    filter(transactionModel.transaction_status.in_([transaction_statuses.lend.submitted_by_borrower,transaction_statuses.sell.pickup_by_buyer])).\
                    all()

        result2 =  db.session.query(bookModel,transactionModel,storeModel).\
                    filter((transactionModel.lender_id == current_user.usernumber)).\
                    filter(transactionModel.book_id == bookModel.book_id).\
                    filter(bookModel.store_id == storeModel.store_id).\
                    filter(transactionModel.transaction_status.in_([transaction_statuses.lend.pickup_by_lender,transaction_statuses.sell.collected_by_seller,transaction_statuses.sell.pickup_by_seller])).\
                    all()

        if result1 or result2 or result1 is not None or result2 is not None:
            if not result1 or result1 is None:
                result = result2
            elif not result2 or result2 is None:
                result = result1
            else:
                result = result1+result2
            for book,transaction,store in result:
                book_dict = book.details()
                book_dict['book_transaction_code'] = transaction.getcodes()
                book_dict['book_transaction_type'] = transaction.transaction_type
                book_dict['book_transaction_status'] = transaction.transaction_status
                book_dict['store'] = store.details()
                booklist.append(book_dict)

            return make_response(
                jsonify(
                    {
                                "message" : "All the previous transactions",
                                "status" : True,
                                "response" : {
                                    "books" : booklist
                                }
                    }
                ),
                200
            )
        else:
            return make_response(
                jsonify(
                    {
                                "message" : "No previous transactions",
                                "status" : False,
                    }
                ),
                200
            )



    ##################################################################################
    # TO DELETE OR REMOVE BOOKS UPLOADED FOR LENDING AND SELLING CURRENTLY
    ##################################################################################
    @app.route('/Book/Uploadedbooks/Remove',methods=['DELETE'])
    @app.route('/Book/Lent/Remove', methods=['DELETE'])
    @app.route('/Book/Sold/Remove', methods=['DELETE'])
    @token_required
    def removeuploadedbook(current_user):

        data = request.get_json()
        book_id = data.get('book_id')

        transaction = transactionModel.query.filter_by(book_id = book_id).first()

        if transaction.transaction_type == Transactiontype.lend.name:
            if transaction.transaction_status == transaction_statuses.lend.uploaded_with_lender:
                transaction.transaction_status = transaction_statuses.lend.pickup_by_lender
                transaction.transaction_lenderpickup_ts = datetime.utcnow()
                transaction.lender_transaction_status = lender_transaction_statuses.lend.removed_by_lender
                transaction.store_transaction_status = store_transaction_statuses.lend.removed_by_lender
                transaction.update()
                return make_response(
                            jsonify({
                            "message" : "Book removed from uploads!",
                            "status" : True,
                            }),
                            201
                        )
                
            elif transaction.transaction_status == transaction_statuses.lend.submitted_by_lender:
                transaction.transaction_status = transaction_statuses.lend.removed_by_lender
                transaction.transaction_return_ts = datetime.utcnow()
                transaction.lender_transaction_status = lender_transaction_statuses.lend.removed_by_lender
                transaction.store_transaction_status = store_transaction_statuses.lend.removed_by_lender
                transaction.update()
                return make_response(
                            jsonify({
                            "message" : "Book will be removed once collected from shop!",
                            "status" : True,
                            }),
                            201
                        )

            else:
                return make_response(
                        jsonify({
                        "message" : "Sorry but the book is being borrowed by someone and so can't be removed!",
                        "status" : False,
                        }),
                        201
                    )
                

        else:
            if transaction.transaction_status == transaction_statuses.sell.uploaded_with_seller:
                transaction.transaction_status = transaction_statuses.sell.pickup_by_seller
                transaction.transaction_lenderpickup_ts = datetime.utcnow()
                transaction.lender_transaction_status = lender_transaction_statuses.sell.removed_by_seller
                transaction.store_transaction_status = store_transaction_statuses.sell.removed_by_seller
                transaction.update()
                return make_response(
                            jsonify({
                            "message" : "Book removed from sold books!",
                            "status" : True,
                            }),
                            201
                        )
                
            elif transaction.transaction_status == transaction_statuses.sell.submitted_by_seller:
                transaction.transaction_status = transaction_statuses.sell.removed_by_seller
                transaction.transaction_return_ts = datetime.utcnow()
                transaction.lender_transaction_status = lender_transaction_statuses.sell.removed_by_seller
                transaction.store_transaction_status = store_transaction_statuses.sell.removed_by_seller
                transaction.update()
                return make_response(
                            jsonify({
                            "message" : "Book will be removed once collected from shop!",
                            "status" : True,
                            }),
                            201
                        )

            else:
                return make_response(
                        jsonify({
                        "message" : "Sorry but the book is being borrowed by someone and so can't be removed!",
                        "status" : False,
                        }),
                        201
                    )

    ##################################################################################
    # TO DELETE OR REMOVE BOOKS BORROWED AND BOOKED FOR BUYING CURRENTLY
    ##################################################################################
    @app.route('/Book/Pickedupbooks/Remove',methods=['POST'])
    @app.route('/Book/Borrowed/Remove', methods = ['DELETE'])
    @app.route('/Book/Bought/Remove', methods=['DELETE'])
    @token_required
    def removeborrowedandbought(current_user):

        data = request.get_json()
        book_id = data.get('book_id')

        transaction = transactionModel.\
                        query.\
                        filter(transactionModel.book_id == book_id).\
                        first()
        

       
        if transaction: 

            if transaction.transaction_type == Transactiontype.lend.name:
                if transaction.transaction_status == transaction_statuses.lend.borrowed_by_borrower :
                    transaction.transaction_status = transaction_statuses.lend.return_by_borrower
                    transaction.update()
                    return make_response(
                        jsonify(
                            {
                                        "message" : "Borrowed book removed please submit to shop!",
                                        "status" : True,
                                        "response" : {
                                            "transaction" : transaction.details()
                                        }
                            }
                        ),
                        202
                    )
                elif transaction.transaction_status == transaction_statuses.lend.pickup_by_borrower :
                    transaction.transaction_status = transaction_statuses.lend.submitted_by_lender
                    transaction.borrower_id = None
                    transaction.update() 
                    return make_response(
                        jsonify(
                            {
                                        "message" : "Borrowed book removed from your pickups!",
                                        "status" : True,
                                        "response" : {
                                            "transaction" : transaction.details()
                                        }
                            }
                        ),
                        202
                    )
                else:
                    return make_response(
                        jsonify(
                            {
                                        "message" : "Book cannot be removed!",
                                        "status" : False,
                                        "response" : {
                                            "transaction" : transaction.details()
                                        }
                            }
                        ),
                        202
                    )
            else:
                if transaction.transaction_status == transaction_statuses.sell.booked_by_buyer :
                    transaction.transaction_status = transaction_statuses.sell.submitted_by_seller
                    transaction.borrower_id = None
                    transaction.update() 
                    return make_response(
                        jsonify(
                            {
                                        "message" : "Borrowed book removed from your pickups!",
                                        "status" : True,
                                        "response" : {
                                            "transaction" : transaction.details()
                                        }
                            }
                        ),
                        202
                    )
                else:
                    return make_response(
                        jsonify(
                            {
                                        "message" : "Book cannot be removed!",
                                        "status" : False,
                                        "response" : {
                                            "transaction" : transaction.details()
                                        }
                            }
                        ),
                        202
                    )
                

        else :
            return make_response(
                jsonify(
                    {
                                "message" : "Error with removing pickup",
                                "status" : True,
                                "response" : {
                                    "transaction" : transaction.details()
                                }
                    }
                ),
                406
            )

    ##################################################################################
    # TO ADD BOOKS AS BORROWED AND BOUGHT
    ##################################################################################
    @app.route('/Book/Pickedupbooks/Add',methods=['POST'])
    @app.route('/Book/Borrowed/Add',methods=['PUT'])
    @app.route('/Book/Bought/Add',methods=['PUT'])
    @token_required
    def addpickedupbooks(current_user):

        data = request.get_json()
        book_id = data.get('book_id')

        transaction = transactionModel.\
                        query.\
                        filter(transactionModel.book_id == book_id).\
                        first()
        

       
        if transaction:
            if transaction.transaction_type == Transactiontype.lend.name: 
                if transaction.transaction_status == transaction_statuses.lend.submitted_by_lender:
                    transaction.transaction_status = transaction_statuses.lend.pickup_by_borrower
                    transaction.borrower_id = current_user.usernumber
                    transaction.borrower_transaction_status = borrower_transaction_statuses.lend.pending
                    transaction.update()
                    return make_response(
                        jsonify(
                            {
                                        "message" : "Book added to pickup please collect it from shop!",
                                        "status" : True,
                                        "response" : {
                                            "transaction" : transaction.details()
                                        }
                            }
                        ),
                        202
                    )
                else:
                    return make_response(
                        jsonify(
                            {
                                        "message" : "Book can't be added to pickup",
                                        "status" : False,
                                        "response" : {
                                            "transaction" : transaction.details()
                                        }
                            }
                        ),
                        202
                    )
            else:
                if transaction.transaction_status == transaction_statuses.sell.submitted_by_seller:
                    transaction.transaction_status = transaction_statuses.sell.booked_by_buyer
                    transaction.borrower_id = current_user.usernumber
                    transaction.borrower_transaction_status = borrower_transaction_statuses.lend.pending
                    transaction.update()
                    return make_response(
                        jsonify(
                            {
                                        "message" : "Book added to pickup please collect it from shop!",
                                        "status" : True,
                                        "response" : {
                                            "transaction" : transaction.details()
                                        }
                            }
                        ),
                        202
                    )
                else:
                    return make_response(
                        jsonify(
                            {
                                        "message" : "Book can't be added to pickup",
                                        "status" : False,
                                        "response" : {
                                            "transaction" : transaction.details()
                                        }
                            }
                        ),
                        202
                    )

        else :
            return make_response(
                jsonify(
                    {
                                "message" : "Error with removing pickup",
                                "status" : True,
                                "response" : {
                                    "transaction" : transaction.details()
                                }
                    }
                ),
                406
            )



    @app.route('/Store/Getstore', methods=['POST'])
    @token_required
    def getstores(current_user):
        
        data = request.get_json()

        longitude = data.get('longitude')
        latitude = data.get('latitude')

        wkt = 'SRID=4326;POINT(%.8f %.8f)' % (longitude,latitude)
        shops = storeModel.query.order_by(Comparator.distance_centroid(storeModel.store_location,func.ST_GeographyFromText(wkt))).limit(10)
        
        retlist = []
        for shop in shops:
            shop_dict = shop.details()
            shop_dict['store_distance'] = shop.getdistance(longitude,latitude)
            retlist.append(shop_dict)


        return make_response(
            jsonify(
                {
                    "message" : "Found the nearest stores",
                    "status" : True,
                    "response" : {
                        "stores" : retlist
                        
                    }
                }
            )
        )



    @app.route('/Store/User', methods=['GET'])
    @token_required_store
    def returnusers(current_user,current_store):
        

        return make_response(
            jsonify(
                {
                    "status" : True,
                    "message" : "The user and store information succesfully accessed",
                    "response" : { 
                                    "user" : current_user.details(),
                                    "store" : current_store.details()
                                } 

                },
            ),
            200
        )

        


    
    
    @app.route('/Store//User/Signup/<string:username>/<string:email>',methods=['GET'])
    @app.route('/Store/User/Signup', methods=['POST'])
    def signupstoreuser(username=None,email=None):
        if request.method == 'POST': 
            data = request.get_json()

            username = data.get('username').lower()
            password = data.get('password')
            email = data.get('email').lower()
            firstname = data.get('firstname').lower()
            lastname = data.get('lastname').lower()
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

            
            user_test = userModel.query.filter((userModel.username == username) | (userModel.email == email)).first()

            if user_test is None:

                user = userModel(
                    username = username,
                    password = generate_password_hash(password),
                    email = email,
                    firstname = firstname,
                    lastname = lastname,
                    dob = dob,
                    phonenumber = phonenumber,
                    created_on=datetime.utcnow(),
                    usertype = Usertype.store.name
                )

                user.insert()
                token = jwt.encode({
                    'usernumber': user.usernumber,
                    'exp': datetime.utcnow() + timedelta(minutes = 30)
                },app.config['SECRET_KEY'],algorithm="HS256")

                url = url_for('verifyuser',token = token,_external=True)
                template = render_template('verifyTokenEmail.html',url = url)
                mail_queue.enqueue(sendverifymail,app.config['AWS_ACCESS_KEY_ID'],app.config['AWS_SECRET_ACCESS_KEY'],app.config['MAILER_ADDRESS'],user.email,template,retry=Retry(max=2))


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
        else:
            if username is None or email is None:
                return make_response(
                    jsonify(
                            {
                                "message" : "Please provide both the information",
                                "status" : False,
                            }
                        ),
                    400,
                    {'WWW-Authenticate' : 'Provide proper information'}
                )
            else:
                user_check = userModel.query.filter((userModel.username == username.lower()) | (userModel.email == email.lower())).first()

                if user_check is None:
                    return make_response(
                        jsonify(
                                {
                                    "message" : "User can be created",
                                    "status" : True,
                                }
                            ),
                        200
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
    


    @app.route('/Store/User/Login', methods=['POST'])
    def storeuserlogin():
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

        data = db.session.query(userModel,storeModel).\
                filter(userModel.username == auth.get('username')).\
                filter(storeModel.usernumber == userModel.usernumber).\
                first()

        if data is None:
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

        user,store = data

        if not user or user.usertype != Usertype.store.name or user is None:
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

        if store is None or not store:
            return make_response( 
                    jsonify(
                        {
                            "message" : "Store not registered with this account please contact booksapp team",
                            "status" : False,
                        }
                    ),
                    401,
                    {'WWW-Authenticate' : 'User does not exist'}
                )


        if check_password_hash(user.password, auth.get('password')):
            emailverified = True
            phoneverified = True
            if not user.email_verified or user.email_verified is None:
                emailverified = False
                token = jwt.encode({
                    'usernumber': user.usernumber,
                    'exp': datetime.utcnow() + timedelta(minutes = 30)
                },app.config['SECRET_KEY'],algorithm="HS256")

                url = url_for('verifyuser',token = token,_external=True)
                template = render_template('verifyTokenEmail.html',url = url)
                mail_queue.enqueue(sendverifymail,app.config['AWS_ACCESS_KEY_ID'],app.config['AWS_SECRET_ACCESS_KEY'],app.config['MAILER_ADDRESS'],user.email,template,retry=Retry(max=2))
                
            if not user.phn_verified or user.phn_verified is None:
                phoneverified = False
                return make_response(
                        jsonify(
                            {
                                "message" : "User is not verified",
                                "status" : False,
                                "response" : {

                                            "emailverified" : emailverified,
                                            "phoneverified" : phoneverified,

                                        }
                            }
                        ),
                        402
                    )
            token = jwt.encode({
                'usernumber': user.usernumber,
                'exp': datetime.utcnow() + timedelta(minutes = 1000)
            },app.config['SECRET_KEY'],algorithm="HS256")

            return make_response(
                jsonify(
                    {
                        "message" : "Log In successfull",
                            "status" : True,
                            "response" : {

                                            "token" : token,
                                            "username" : user.username,
                                            "usernumber" : user.usernumber,
                                            "store_id" : store.store_id,
                                            "emailverified" : emailverified,
                                            "phoneverified" : phoneverified
                                        }

                    }
                )
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
        

    ##################################################################################
    # TO GET ALL THE BOOKS FOR PICKUP AT STORE
    ##################################################################################    
    @app.route('/Store/Books/Pickups', methods=['GET'])
    @token_required_store
    def getpickups(current_user,current_store):

        store_id = current_store.store_id

        

        result =  db.session.query(bookModel,transactionModel).\
                    filter(transactionModel.store_id == store_id).\
                    filter(transactionModel.book_id == bookModel.book_id).\
                    filter(transactionModel.transaction_status.in_([transaction_statuses.lend.pickup_by_borrower,transaction_statuses.lend.submitted_by_borrower,transaction_statuses.lend.removed_by_lender,transaction_statuses.sell.pickup_by_buyer,transaction_statuses.sell.removed_by_seller,transaction_statuses.sell.booked_by_buyer])).\
                    all()

        if not result or result is None: 
            return make_response( 
                                jsonify(
                                    {
                                        "message" : "No pickups right now",
                                        "status" : True,
                                    }
                                ),
                                200,
                            )
        else :
            pickup_book_list = []
            for book,transaction in result:
                book_dict = book.details()
                book_dict['book_transaction_code'] = transaction.getcodes()
                book_dict['book_transaction_type'] = transaction.transaction_type
                pickup_book_list.append(book_dict)

            return make_response( 
                            jsonify(
                                {
                                    "message" : "All the books to be picked up",
                                    "status" : True,
                                    "response" : {
                                        "pickup_book_list" : pickup_book_list
                                    }
                                }
                            ),
                            200,
                        )


    ##################################################################################
    # TO GET ALL THE BOOKS FOR DROPOFFS AT STORE
    ################################################################################## 
    @app.route('/Store/Books/Dropoffs', methods=['GET'])
    @token_required_store
    def getdropoffs(current_user,current_store):

        store_id = current_store.store_id

        
        result =  db.session.query(bookModel,transactionModel).\
                    filter(transactionModel.store_id == store_id).\
                    filter(transactionModel.book_id == bookModel.book_id).\
                    filter(transactionModel.transaction_status.in_([transaction_statuses.lend.uploaded_with_lender,transaction_statuses.lend.return_by_borrower,transaction_statuses.sell.uploaded_with_seller])).\
                    all()

        if not result or result is None: 
            return make_response( 
                                jsonify(
                                    {
                                        "message" : "No dropoffs right now",
                                        "status" : True,
                                    }
                                ),
                                200,
                            )
        else :
            dropoff_book_list = []
            for book,transaction in result:
                book_dict = book.details()
                book_dict['book_transaction_code'] = transaction.getcodes()
                book_dict['book_transaction_type'] = transaction.transaction_type
                dropoff_book_list.append(book_dict)

            return make_response( 
                            jsonify(
                                {
                                    "message" : "All the books to be dropped off",
                                    "status" : True,
                                    "response" : {
                                        "dropoff_book_list" : dropoff_book_list
                                    }
                                }
                            ),
                            200,
                        )
                        
    ##################################################################################
    # TO GET ALL THE BOOKS IDLE AT THE STORE
    ##################################################################################             
    @app.route('/Store/Books/Idlebooks', methods=['GET'])
    @token_required_store
    def getallbooks(current_user,current_store):
        store_id = current_store.store_id


        result =  db.session.query(bookModel,transactionModel).\
                    filter(transactionModel.store_id == store_id).\
                    filter(transactionModel.book_id == bookModel.book_id).\
                    filter(transactionModel.transaction_status.in_([transaction_statuses.lend.submitted_by_lender,transaction_statuses.sell.submitted_by_seller])).\
                    all()

        if not result or result is None: 
            return make_response( 
                                jsonify(
                                    {
                                        "message" : "No books are idle",
                                        "status" : True,
                                    }
                                ),
                                200,
                            )
        else :
            book_list = []
            for book,transaction in result:
                book_dict = book.details()
                book_dict['book_transaction_code'] = transaction.getcodes()
                book_dict['book_transaction_type'] = transaction.transaction_type
                book_list.append(book_dict)

            return make_response( 
                            jsonify(
                                {
                                    "message" : "All the books in the store",
                                    "status" : True,
                                    "response" : {
                                        "book_list" : book_list
                                    }
                                }
                            ),
                            200,
                        )
        

    @app.route('/Store/Transaction/Dropoffpricing', methods=['POST'])
    @token_required_store
    def dropoffpricing(current_user,current_store):
        data = request.get_json()
        store_id = current_store.store_id
        book_id = data.get('book_id')

        transaction =   transactionModel.\
                        query.\
                        filter(transactionModel.book_id == book_id).\
                        filter(transactionModel.store_id == store_id).\
                        filter( transactionModel.transaction_status.in_([transaction_statuses.lend.uploaded_with_lender,transaction_statuses.lend.return_by_borrower,transaction_statuses.sell.uploaded_with_seller]) ).\
                        first()
        
        if transaction is not None:
            pricing = transaction.getdropoffpricing()

            return make_response( 
                                    jsonify(
                                        {
                                            "message" : "Dropoff pricing!",
                                            "status" : True,
                                            "response" : {
                                                "pricing" : pricing
                                            }
                                        }
                                    ),
                                    200,
                                )
        else :
            return make_response( 
                                    jsonify(
                                        {
                                            "message" : "Cant give you dropoff pricing!",
                                            "status" : False,
                                        }
                                    ),
                                    200,
                                )


    @app.route('/Store/Transaction/Confirmdropoff', methods=['POST'])
    @token_required_store
    def confirmdropoff(current_user,current_store):
        data = request.get_json()
        store_id = current_store.store_id
        book_id = data.get('book_id')

        transaction =   transactionModel.\
                        query.\
                        filter(transactionModel.book_id == book_id).\
                        filter(transactionModel.store_id == store_id).\
                        filter( transactionModel.transaction_status.in_([transaction_statuses.lend.uploaded_with_lender,transaction_statuses.lend.return_by_borrower,transaction_statuses.sell.uploaded_with_seller]) ).\
                        first()

        if transaction is None: 
            return make_response( 
                                jsonify(
                                    {
                                        "message" : "Error in transaction can't confirm dropoff!",
                                        "status" : True,
                                    }
                                ),
                                200,
                            )
        else : 
            if transaction.transaction_type == Transactiontype.lend.name:
                if transaction.transaction_status == transaction_statuses.lend.uploaded_with_lender : 
                    transaction.transaction_status = transaction_statuses.lend.submitted_by_lender
                    transaction.transaction_submit_ts = datetime.utcnow()
                    transaction.update()

                elif transaction.transaction_status == transaction_statuses.lend.return_by_borrower :
                    transaction.transaction_status = transaction_statuses.lend.submitted_by_borrower
                    transaction.store_transaction_status = store_transaction_statuses.lend.dropoff_by_borrower
                    transaction.borrower_transaction_status = borrower_transaction_statuses.lend.dropoff_by_borrower
                    transaction.transaction_return_ts = datetime.utcnow()
                    transaction.update()
                
                return make_response( 
                                    jsonify(
                                        {
                                            "message" : "Dropoff confirmed!",
                                            "status" : True,
                                            "response" : {
                                                "transaction" : transaction.details()
                                            }
                                        }
                                    ),
                                    200,
                                )
            else:
                transaction.transaction_status = transaction_statuses.sell.uploaded_with_seller
                transaction.transaction_submit_ts = datetime.utcnow()
                transaction.update()

                return make_response( 
                                    jsonify(
                                        {
                                            "message" : "Dropoff confirmed!",
                                            "status" : True,
                                            "response" : {
                                                "transaction" : transaction.details()
                                            }
                                        }
                                    ),
                                    200,
                                )

    @app.route('/Store/Transaction/Pickuppricing', methods=['POST'])
    @token_required_store
    def pickuppricing(current_user,current_store):
        data = request.get_json()
        store_id = current_store.store_id
        book_id = data.get('book_id')

        transaction =   transactionModel.\
                        query.\
                        filter(transactionModel.book_id == book_id).\
                        filter(transactionModel.store_id == store_id).\
                        filter(transactionModel.transaction_status.in_([transaction_statuses.lend.submitted_by_borrower,transaction_statuses.lend.removed_by_lender,transaction_statuses.lend.pickup_by_borrower,transaction_statuses.sell.pickup_by_buyer,transaction_statuses.sell.removed_by_seller,transaction_statuses.sell.booked_by_buyer])).\
                        first()
        
        if transaction is not None:
            pricing = transaction.getpickuppricing()

            return make_response( 
                                    jsonify(
                                        {
                                            "message" : "Pickup confirmed!",
                                            "status" : True,
                                            "response" : {
                                                "pricing" : pricing
                                            }
                                        }
                                    ),
                                    200,
                                )
        else:
            return make_response( 
                                    jsonify(
                                        {
                                            "message" : "Can't show you pickup pricing!",
                                            "status" : False,
                                        }
                                    ),
                                    200,
                                )

    @app.route('/Store/Transaction/Confirmpickup', methods=['POST'])
    @token_required_store
    def confirmpickup(current_user,current_store):

        data = request.get_json()

        store_id = current_store.store_id
        book_id = data.get('book_id')

        transaction =   transactionModel.\
                        query.\
                        filter(transactionModel.book_id == book_id).\
                        filter(transactionModel.store_id == store_id).\
                        filter(transactionModel.transaction_status.in_([transaction_statuses.lend.submitted_by_borrower,transaction_statuses.lend.removed_by_lender,transaction_statuses.lend.pickup_by_borrower,transaction_statuses.sell.pickup_by_buyer,transaction_statuses.sell.removed_by_seller,transaction_statuses.sell.booked_by_buyer])).\
                        first()

        if not transaction : 
            return make_response( 
                                jsonify(
                                    {
                                        "message" : "Error in transaction can't confirm pickup!",
                                        "status" : True,
                                    }
                                ),
                                200,
                            )
        else :
            if transaction.transaction_type == Transactiontype.lend.name:
                if transaction.transaction_status == transaction_statuses.lend.pickup_by_borrower: 
                    transaction.transaction_status = transaction_statuses.lend.borrowed_by_borrower
                    transaction.borrower_transaction_status = borrower_transaction_statuses.lend.pickup_by_borrower
                    transaction.transaction_pickup_ts = datetime.utcnow()
                    transaction.update()

                elif transaction.transaction_status == transaction_statuses.lend.submitted_by_borrower:
                    transaction.transaction_status = transaction_statuses.lend.pickup_by_lender
                    transaction.lender_transaction_status = lender_transaction_statuses.lend.pickup_by_lender
                    transaction.store_transaction_status = store_transaction_statuses.lend.pickup_by_lender
                    transaction.transaction_lenderpickup_ts = datetime.utcnow()
                    transaction.update()

                elif transaction.transaction_status == transaction_statuses.lend.removed_by_lender:
                    transaction.transaction_status = transaction_statuses.lend.pickup_by_lender
                    transaction.transaction_lenderpickup_ts = datetime.utcnow()
                    transaction.update()

                return make_response( 
                                    jsonify(
                                        {
                                            "message" : "Pickup confirmed!",
                                            "status" : True,
                                            "response" : {
                                                "transaction" : transaction.details()
                                            }
                                        }
                                    ),
                                    200,
                                )
            else:
                if transaction.transaction_status == transaction_statuses.sell.booked_by_buyer: 
                    transaction.transaction_status = transaction_statuses.sell.pickup_by_buyer
                    transaction.borrower_transaction_status = borrower_transaction_statuses.sell.pickup_by_borrower
                    transaction.transaction_pickup_ts = datetime.utcnow()
                    transaction.update()

                elif transaction.transaction_status == transaction_statuses.sell.pickup_by_buyer:
                    transaction.transaction_status = transaction_statuses.sell.collected_by_seller
                    transaction.lender_transaction_status = lender_transaction_statuses.sell.collected_by_seller
                    transaction.store_transaction_status = store_transaction_statuses.sell.collected_by_seller
                    transaction.transaction_lenderpickup_ts = datetime.utcnow()
                    transaction.update()

                elif transaction.transaction_status == transaction_statuses.sell.removed_by_seller:
                    transaction.transaction_status = transaction_statuses.sell.pickup_by_seller
                    transaction.transaction_lenderpickup_ts = datetime.utcnow()
                    transaction.update()

                return make_response( 
                                    jsonify(
                                        {
                                            "message" : "Pickup confirmed!",
                                            "status" : True,
                                            "response" : {
                                                "transaction" : transaction.details()
                                            }
                                        }
                                    ),
                                    200,
                                )




    @app.route('/Store/Transaction/Pendingpayments', methods=['GET'])
    @token_required_store
    def pendingpayments(current_user,current_store):

        store_id = current_store.store_id

        transactions =   transactionModel.\
                        query.\
                        filter(transactionModel.store_id == store_id).\
                        filter(transactionModel.store_transaction_status.in_([store_transaction_statuses.lend.pickup_by_lender,transaction_statuses.sell.collected_by_seller,store_transaction_statuses.sell.transaction_invoiced,store_transaction_statuses.lend.transaction_invoiced])).\
                        all()


        return make_response( 
                                jsonify(
                                    {
                                        "message" : "All the pending payments!",
                                        "status" : True,
                                        "response" : {
                                            "transactions" : transactions
                                        }
                                    }
                                ),
                                200,
                            )


    @app.route('/Store/Transaction/Invoices', methods=['GET'])
    @token_required_store
    def storeinvoices(current_user,current_store):

        store_id = current_store.store_id

        invoices =   invoiceModel.query.\
                        filter(invoiceModel.store_id == store_id).\
                        order_by(invoiceModel.invoice_date.desc()).\
                        all()


        return make_response( 
                                jsonify(
                                    {
                                        "message" : "All the pending payments!",
                                        "status" : True,
                                        "response" : {
                                            "invoices" : invoices
                                        }
                                    }
                                ),
                                200,
                            )

    @app.route('/Store/Transaction/Invoices/<int:invoice_id>/Transactions', methods=['GET'])
    @token_required_store
    def storeinvoicestransactions(current_user,current_store,invoice_id):

        store_id = current_store.store_id


        if invoice_id != None:
            invoice = invoiceModel.query.filter(invoiceModel.invoice_id == invoice_id).filter(invoiceModel.store_id == store_id).first()

            if invoice and invoice is not None:
                transactions = transactionModel.query.filter(transactionModel.invoice_id == invoice.invoice_id).all()
                
                return make_response( 
                                        jsonify(
                                            {
                                                "message" : "All the transactions!",
                                                "status" : True,
                                                "response" : {
                                                    "transactions" : transactions
                                                }
                                            }
                                        ),
                                        200,
                                    )


        return make_response( 
                                        jsonify(
                                            {
                                                "message" : "Can't get transactions for given invoice id!",
                                                "status" : False,
                                            }
                                        ),
                                        404,
                                    )


        

    @app.route('/Admin',methods=['GET'])
    @app.route('/Admin/Login', methods=['POST'])
    def adminlogin():
        auth = request.form

        if not auth or not auth.get('username') or not auth.get('password'):
            return render_template('login.html',error = 'Login required')


        user = userModel.query.filter_by(username = auth.get('username')).first()

        if not user or user.usertype != Usertype.admin.name:
            return render_template('login.html',error = 'Check username')
        elif user.email_verified and user.email_verified != None:
            
            if check_password_hash(user.password, auth.get('password')):
                token = jwt.encode({
                    'usernumber': user.usernumber,
                    'exp': datetime.utcnow() + timedelta(minutes = 1000)
                },app.config['SECRET_KEY'],algorithm="HS256")
                session['x-access-token'] = token

                store = storeModel.query.filter_by(usernumber = user.usernumber).first()
                return render_template('admin-index.html',error = 'Correct password')
            else:
                return render_template('login.html',error = 'Incorrect password')


    @app.route('/Admin/<template>',methods=['GET'])
    @token_required_admin
    def adminloader(user,template):
        try:

            if not template.endswith('.html'):
                template += '.html'
            return render_template(template)

        except TemplateNotFound:
            return render_template('404.html'), 404

        except:
            return render_template('404.html'), 500
            

    @app.route('/Admin/User',methods=['GET'])
    @app.route('/Admin/User/<int:userid>',methods=['GET'])
    @token_required_admin
    def admingetuser(user,userid=None):
        username = request.args.get('username')
        email = request.args.get('email')
        success = False

        if username == "" and email == "" and userid == None:
            return render_template('user-profile.html',success = success)
        else:
            user = userModel.query.\
                    filter((userModel.username == username) | (userModel.email == email) | (userModel.usernumber == userid)).\
                    filter(userModel.usertype == Usertype.user.name).\
                    first()
                    
            if user and user != None:
                success = True
                uploadedbooks = bookModel.query.filter(bookModel.usernumber == user.usernumber).all()

                books_lent_previously = transactionModel.query.\
                                        filter(transactionModel.lender_id == user.usernumber).\
                                        filter(transactionModel.transaction_status == transaction_statuses.lend.pickup_by_lender).\
                                        order_by(transactionModel.transaction_upload_ts.desc()).\
                                        all()
                books_lent_currently = transactionModel.query.\
                                        filter(transactionModel.lender_id == user.usernumber).\
                                        filter(transactionModel.transaction_status.notin_([transaction_statuses.lend.uploaded_with_lender,transaction_statuses.lend.removed_by_lender,transaction_statuses.lend.submitted_by_lender,transaction_statuses.lend.submitted_by_borrower,transaction_statuses.lend.pickup_by_lender])).\
                                        order_by(transactionModel.transaction_upload_ts.desc()).\
                                        all() 
                books_lent_pickup = transactionModel.query.\
                                        filter(transactionModel.lender_id == user.usernumber).\
                                        filter(transactionModel.transaction_status.in_([transaction_statuses.lend.removed_by_lender,transaction_statuses.lend.submitted_by_borrower])).\
                                        order_by(transactionModel.transaction_upload_ts.desc()).\
                                        all() 

                books_lent_dropoff_or_notborrowed = transactionModel.query.\
                                        filter(transactionModel.lender_id == user.usernumber).\
                                        filter(transactionModel.transaction_status.in_([transaction_statuses.lend.uploaded_with_lender,transaction_statuses.lend.submitted_by_lender])).\
                                        order_by(transactionModel.transaction_upload_ts.desc()).\
                                        all()

                books_borrowed_previously = transactionModel.query.\
                                            filter(transactionModel.borrower_id == user.usernumber).\
                                            filter(transactionModel.transaction_status == transaction_statuses.lend.submitted_by_borrower).\
                                            order_by(transactionModel.transaction_upload_ts.desc()).\
                                            all()

                books_borrowed_currently = transactionModel.query.\
                                            filter(transactionModel.borrower_id == user.usernumber).\
                                            filter(transactionModel.transaction_status == transaction_statuses.lend.borrowed_by_borrower).\
                                            order_by(transactionModel.transaction_upload_ts.desc()).\
                                            all()

                books_borrowed_pickup = transactionModel.query.\
                                            filter(transactionModel.borrower_id == user.usernumber).\
                                            filter(transactionModel.transaction_status == transaction_statuses.lend.pickup_by_borrower).\
                                            order_by(transactionModel.transaction_upload_ts.desc()).\
                                            all()

                books_borrowed_dropoff = transactionModel.query.\
                                            filter(transactionModel.borrower_id == user.usernumber).\
                                            filter(transactionModel.transaction_status == transaction_statuses.lend.return_by_borrower).\
                                            order_by(transactionModel.transaction_upload_ts.desc()).\
                                            all()

                borrowedbookslist = set(transaction.book_id for transaction in books_borrowed_previously+books_borrowed_currently+books_borrowed_pickup+books_borrowed_dropoff)

                borrowedbooks = bookModel.query.filter(bookModel.book_id.in_(borrowedbookslist)).all()

                tables = {
                    "Books Lent Previously" : books_lent_previously,
                    "Books lent currently" : books_lent_currently,
                    "Lent books ready for pickup" : books_lent_pickup,
                    "Lent books ready for dropoff or being borrowed" : books_lent_dropoff_or_notborrowed,
                    "Books borrowed previously" : books_borrowed_previously,
                    "Books borrowed currently" : books_borrowed_currently,
                    "Borrowed books ready for pickup" : books_borrowed_pickup,
                    "Borrowed books ready for dropoff" : books_borrowed_dropoff
                }
                
                return render_template('user-profile.html',
                                        success=success,
                                        user=user,
                                        uploadedbooks=uploadedbooks,
                                        borrowedbooks=borrowedbooks,
                                        tables = tables
                                    )
            else:
                return render_template('user-profile.html',success = success)

    @app.route('/Admin/Store',methods=['GET'])
    @app.route('/Admin/Store/<int:store_id>',methods=['GET'])
    @token_required_admin
    def admingetstore(user,store_id = None):
        username = request.args.get('username')
        email = request.args.get('email')
        success = False

        user = None
        store = None
        if  store_id != None:
            store = storeModel.query.\
                    filter( (storeModel.store_id == store_id) ).\
                    first()
            if store and store != None:
                user = userModel.query.\
                        filter( (userModel.usernumber == store.usernumber) ).\
                        first()
                success = True  

        elif username != "" or email != "" :
            user = userModel.query.\
                    filter( (userModel.username == username) | (userModel.email == email) ).\
                    filter(userModel.usertype == Usertype.store.name).\
                    first()
            if user and user != None:
                store = storeModel.query.\
                        filter( (storeModel.usernumber == user.usernumber) ).\
                        first()
                success = True 

        else :
            return render_template('store-profile.html',success = success)   

        if success == True:
            idle_books = transactionModel.query.\
                        filter(transactionModel.store_id == store.store_id).\
                        filter(transactionModel.transaction_status == transaction_statuses.lend.submitted_by_lender).\
                        order_by(transactionModel.transaction_upload_ts.desc()).\
                        all()
                        
            pickup_books = transactionModel.query.\
                        filter(transactionModel.store_id == store.store_id).\
                        filter(transactionModel.transaction_status.in_([transaction_statuses.lend.pickup_by_borrower,transaction_statuses.lend.submitted_by_borrower,transaction_statuses.lend.removed_by_lender])).\
                        order_by(transactionModel.transaction_upload_ts.desc()).\
                        all()

            dropoff_books = transactionModel.query.\
                        filter(transactionModel.store_id == store.store_id).\
                        filter(transactionModel.transaction_status.in_([transaction_statuses.lend.uploaded_with_lender,transaction_statuses.lend.return_by_borrower])).\
                        order_by(transactionModel.transaction_upload_ts.desc()).\
                        all()

            past_books = transactionModel.query.\
                        filter(transactionModel.store_id == store.store_id).\
                        filter(transactionModel.transaction_status == transaction_statuses.lend.pickup_by_lender).\
                        order_by(transactionModel.transaction_upload_ts.desc()).\
                        all()

            all_books_info = bookModel.query.\
                            filter(bookModel.store_id == store.store_id).\
                            all()

            invoices = invoiceModel.query.\
                        filter(invoiceModel.store_id == store.store_id).\
                        order_by(invoiceModel.invoice_date.desc()).\
                        all()
                            

            tables = {
                'Books idle at the store' : idle_books,
                'Books to be picked up' : pickup_books,
                'Books that will be dropped off' : dropoff_books,
                "Past transactions" : past_books
            }

            return render_template('store-profile.html',
                                    success = success,
                                    store = store,
                                    user = user,
                                    all_books_info = all_books_info,
                                    invoices = invoices,
                                    tables = tables
                                )  
        else:
            return render_template('store-profile.html',success = success)  


    @app.route('/Admin/Store/Signup', methods=['POST'])
    @token_required_admin
    def signupstore(user):

        data = request.form

        username = data.get('username')
        current_user = userModel.query.\
                        filter(userModel.username == username).\
                        first()

        if not current_user or current_user == None:
            return render_template('store-registration.html', error = "User doesn't exist check username", status = False)

        if current_user.usertype != Usertype.store.name:
            return render_template('store-registration.html', error = "User is not authorized to signup for store!", status = False)

        if not current_user.email_verified or current_user.email_verified == None:
            token = jwt.encode({
                'usernumber': current_user.usernumber,
                'exp': datetime.utcnow() + timedelta(minutes = 30)
            },app.config['SECRET_KEY'],algorithm="HS256")

            url = url_for('verifyuser',token = token,_external=True)
            template = render_template('verifyTokenEmail.html',url = url)
            mail_queue.enqueue(sendverifymail,app.config['AWS_ACCESS_KEY_ID'],app.config['AWS_SECRET_ACCESS_KEY'],app.config['MAILER_ADDRESS'],user.email,template,retry=Retry(max=2))

            return render_template('store-registration.html', error = "User is not verified yet", status = False)
            
        store_check = storeModel.query.filter(storeModel.usernumber == current_user.usernumber).first()

        if not store_check or store_check != None:
            return render_template('store-registration.html', error = "User is already signed up with a store", status = False)

        
        usernumber = current_user.usernumber
        store_name = data.get('store_name')
        store_incharge = current_user.firstname+" "+current_user.lastname
        store_address = data.get('store_address')
        store_pincode = data.get('store_pincode')
        store_number = data.get('store_number')
        store_longitude = data.get('longitude')
        store_latitude = data.get('latitude')

        store = storeModel(
            usernumber= usernumber,
            store_name= store_name,
            store_incharge= store_incharge,
            store_address= store_address,
            store_pincode = store_pincode,
            store_number = store_number,
            store_location = 'SRID=4326;POINT(%.8f %.8f)' % (store_longitude,store_latitude),
            store_latitude= store_latitude,
            store_longitude= store_longitude,
        )

        store.insert()


        return render_template('store-registration.html', error = "Store Signed Up!", status = True, store_id = store.store_id) 
            

                

                    
            


    @app.route('/Admin/Book/<int:book_id>',methods=['GET'])
    @token_required_admin
    def admingetbook(user,book_id = None):

        if book_id != None:
            book = bookModel.query.filter_by(book_id = book_id).first()

            if book and book!= None:
                return render_template('bookinfo.html',book = book)
    
        return render_template('404.html')


    


    @app.route('/Admin/Transaction/<int:transaction_id>',methods=['GET'])
    @token_required_admin
    def admingettransaction(user,transaction_id = None):

        if transaction_id != None:
            transaction = transactionModel.query.filter_by(transaction_id = transaction_id).first()

            if transaction and transaction!= None:
                return render_template('transactioninfo.html',transaction = transaction)
    
        return render_template('404.html')


    @app.route('/Admin/Store/Generateinvoice/<int:store_id>',methods=['GET'])
    @token_required_admin
    def generatestoreinvoice(admin,store_id = None):

        if store_id is not None:
            store = storeModel.query.filter_by(store_id = store_id).first()
            pending_transactions = transactionModel.query.\
                                    filter(transactionModel.store_id == store_id).\
                                    filter(transactionModel.store_transaction_status == store_transaction_statuses.lend.pickup_by_lender).\
                                    order_by(transactionModel.transaction_upload_ts.desc()).\
                                    all()
                                    
            if store and store is not None and pending_transactions and pending_transactions is not None:
                invoice = invoiceModel(
                    store_id= store.store_id,
                    invoice_status= invoice_statuses.pending,
                    invoice_date= datetime.utcnow()
                )
                invoice.insert()

                total = 0
                for transactions in pending_transactions:
                    total += transactions.store_cost
                    transactions.store_transaction_status = store_transaction_statuses.lend.transaction_invoiced
                    transactions.invoice_id = invoice.invoice_id
                    transactions.update()



                filename = generateBill(admin,store,pending_transactions,invoice,app.config['AWS_ACCESS_KEY_ID'],app.config['AWS_SECRET_ACCESS_KEY'],app.config['BUCKET'])

                invoice.invoice_url = app.config['INVOICE_BUCKET_LINK'] + filename
                invoice.invoice_total = total
                invoice.update()

                return redirect(invoice.invoice_url)
            else:
                return render_template('404.html')
    
        return render_template('404.html')

    
    @app.route('/Admin/Invoice/<int:invoice_id>',methods=['GET'])
    @token_required_admin
    def admingetinvoice(user,invoice_id = None):

        if invoice_id != None:
            invoice = invoiceModel.query.filter_by(invoice_id = invoice_id).first()

            if invoice and invoice!= None:
                transactions = transactionModel.query.filter(transactionModel.invoice_id == invoice.invoice_id).all()
                return render_template('invoiceinfo.html',transactions = transactions,invoice = invoice)
    
        return render_template('404.html')

    @app.route('/Admin/Store/Confirmpayment',methods=['POST'])
    @token_required_admin
    def confirmpayment(user):

        invoice_id = request.form.get('invoice_id')
        if invoice_id != None:
            invoice = invoiceModel.query.filter_by(invoice_id = invoice_id).first()

            if invoice and invoice!= None:
                if invoice.invoice_status == invoice_statuses.paid:
                    return render_template('store-confirmpayment.html',status = True, error = "This Invoice is already paid!", invoice_id= invoice.invoice_id)
                else:
                    invoice.invoice_status = invoice_statuses.paid
                    invoice.payment_date = datetime.utcnow()
                    invoice.confirmed_usernumber = user.usernumber
                    invoice.update()

                    transactions = transactionModel.query.filter(transactionModel.invoice_id == invoice.invoice_id).all()
                    for transac in transactions:
                        transac.store_transaction_status = store_transaction_statuses.lend.payment_collected
                        transac.update()
                    return render_template('store-confirmpayment.html',status = True,error = "Payment Confirmed!", invoice_id = invoice.invoice_id)

            else:
                return render_template('store-confirmpayment.html',status = False, error = "No such Invoice ID found!")

        return render_template('store-confirmpayment.html',status = False, error = "Please fill the form correctly!")


    @app.route('/',methods=['GET'])
    def homepage():
        return render_template('index.html')

    


    return app



app = create_app()


if __name__ == "__main__":
    
    port = int(os.environ.get("PORT",5000))
    app.run(host='127.0.0.1',port=port,debug = True)
