import os
from flask import Flask,render_template, request, abort, jsonify ,make_response
from flask_cors import CORS
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.sql.type_api import NULLTYPE
from models import setup_db, storeModel, transactionModel, userModel,bookModel, db_drop_and_create_all , db
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import uuid
from  werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta,date
from s3_functions import upload_file
from werkzeug.utils import secure_filename
import boto3
from status import transaction_statuses,lender_transaction_statuses,store_transaction_statuses,borrower_transaction_statuses
from geoalchemy2.types import Geometry
from geoalchemy2.comparator import Comparator
import geoalchemy2.functions as func
from transactioncodes import getcodes






temp = [{"hello" : "Why are you"},{"hello2" : "how are ypo2"}]

BUCKET = "booksapp-image-data"
BOOK_UPLOAD_FOLDER = "uploads"
BUCKET_LINK = "https://"+BUCKET+".s3.ap-south-1.amazonaws.com/book-image-folder/"

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



    @app.route('/Book/Upload',methods=['POST'])
    @token_required
    def uploadbook(current_user):
        book_name = request.form.get("book_name")
        book_year = request.form.get("book_year")
        book_condition = request.form.get("book_condition")
        book_img = request.files['book_img']
        book_price = request.form.get('book_price')
        store_id = request.form.get('store_id')
        usernumber = current_user.usernumber
        book_author = request.form.get('book_author')

        filename = secure_filename("book-"+datetime.utcnow().strftime("%m-%d-%Y_%H:%M:%S")+".jpg")
        upload_file(filename,BUCKET,body=book_img)
        
        book_img_url = BUCKET_LINK+filename

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


        transaction = transactionModel(
            book_id= book.book_id,
            transaction_status= transaction_statuses.uploaded_with_lender,
            lender_id= usernumber,
            store_id= store_id,
            borrower_id= None,
            lender_transaction_status= lender_transaction_statuses.pending,
            store_transaction_status= store_transaction_statuses.pending,
            borrower_transaction_status = borrower_transaction_statuses.pending,
            book_price= book_price,
            transaction_upload_ts= datetime.now(),
            transaction_submit_ts= None,
            transaction_pickup_ts= None,
            transaction_return_ts= None,
            transaction_lenderpickup_ts= None,
        )

        transaction.insert()


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



    @app.route('/Book/Uploadedbooks',methods=['POST'])
    @token_required
    def uploadedbooks(current_user):

        books = bookModel.query.filter_by(usernumber = current_user.usernumber).all()
        

        booklist = [] 

        for book in books:
            status = transactionModel.query.filter_by(book_id = book.book_id).first()
            if status.transaction_status != transaction_statuses.pickup_by_lender:
                book_dict = book.details()
                book_dict['book_status'] = status.transaction_status
                book_dict['book_transaction_code'] = getcodes(status)
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


    @app.route('/Book/Uploadedbooks/Edit',methods=['PUT'])
    @token_required
    def edituploadedbook(current_user):

        data = request.get_json()
        book_id = data.get('book_id')
        book_name = data.get('book_name')
        book_author = data.get('book_author')
        book_price = data.get('book_price')
        book_condition = data.get('book_condition')
        book_year = data.get('book_year')

        book = bookModel.query.filter_by(book_id = book_id).first()

        book.book_name = book_name
        book.book_author = book_author
        book.book_price = book_price
        book.book_condition = book_condition
        book.book_year = book_year

        book.update()

        return make_response(
            jsonify(
                {
                            "message" : "Book Updated",
                            "status" : True,
                            "response" : {
                                "book" : book.details(),
                            }
                }
            ),
            201
        )


    @app.route('/Book/Uploadedbooks/Remove',methods=['DELETE'])
    @token_required
    def removeuploadedbook(current_user):

        data = request.get_json()
        book_id = data.get('book_id')

        ret = {
            "message" : "Sorry but the book is being borrowed by someone and so can't be removed!",
            "status" : False,
        }

        transaction = transactionModel.query.filter_by(book_id = book_id).first()

        if transaction.transaction_status == transaction_statuses.uploaded_with_lender:
            transaction.transaction_status = transaction_statuses.pickup_by_lender
            transaction.transaction_lenderpickup_ts = datetime.utcnow()
            transaction.lender_transaction_status = lender_transaction_statuses.removed_by_lender
            transaction.store_transaction_status = store_transaction_statuses.removed_by_lender
            transaction.update()
            ret["message"] = "Book removed from uploads!"
            ret["status"] = True
            
        elif transaction.transaction_status == transaction_statuses.submitted_by_lender:
            transaction.transaction_status = transaction_statuses.removed_by_lender
            transaction.transaction_return_ts = datetime.utcnow()
            transaction.lender_transaction_status = lender_transaction_statuses.removed_by_lender
            transaction.store_transaction_status = store_transaction_statuses.removed_by_lender
            transaction.update()
            ret["message"] = "Book will be removed once collected from shop!"
            ret["status"] = True
            
        return make_response(
            jsonify(ret),
            201
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
            shop_wkt = 'SRID=4326;POINT(%.8f %.8f)' % (shop_dict['store_longitude'],shop_dict['store_latitude'])
            shop_dict['store_distance'] = db.session.query(func.ST_Distance(func.ST_GeographyFromText(wkt),func.ST_GeographyFromText(shop_wkt))).first()
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



    @app.route('/Store/User', methods=['POST'])
    @token_required
    def returnusers(current_user):
        data = request.get_json()

        store_id = data.get('store_id')

        store = storeModel.query.filter_by(store_id = store_id).first()

        return make_response(
            jsonify(
                {
                    "status" : True,
                    "message" : "The user and store information succesfully accessed",
                    "response" : { 
                                    "user" : current_user.details(),
                                    "store" : store.details()
                                } 

                },
            ),
            200
        )

        


    @app.route('/Store/User/Signup', methods=['POST'])
    @token_required
    def signupstore(current_user):

        data = request.get_json()
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


        return make_response(
            jsonify(
                {
                            "message" : "Store Signed up",
                            "status" : True,
                            "response" : {
                                "store" : store.details()
                            }
                }
            ),
            200
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
        else:
            store = storeModel.query.filter_by(usernumber = user.usernumber).first()

            if not store:
                return make_response(
                    jsonify(
                        {
                            "message" : "User is not a registered store",
                            "status" : False,
                        }
                    ),
                    401,
                    {'WWW-Authenticate' : "User is not a registered store"}
                )
            else :
                if check_password_hash(user.password, auth.get('password')):
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
                                                    "store_id" : store.store_id 
                                                }
                                }
                            ),
                            201
                        )
                else:
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


        
    @app.route('/Store/transaction/pickups', methods=['POST'])
    @token_required
    def getpickups(current_user):
        data = request.get_json()

        store_id = data.get('store_id')

        pickup_books = transactionModel.\
                        query.\
                        filter(transactionModel.store_id == store_id).\
                        filter( (transactionModel.transaction_status == transaction_statuses.pickup_by_borrower) | (transactionModel.transaction_status == transaction_statuses.submitted_by_borrower) | (transactionModel.transaction_status == transaction_statuses.removed_by_lender) ).\
                        all()

        if not pickup_books: 
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
            for book in pickup_books:
                b = bookModel.query.filter_by(book_id = book.book_id).first()
                book_dict = b.details()
                book_dict['book_transaction_code'] = getcodes(book)
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


    @app.route('/Store/transaction/dropoffs', methods=['POST'])
    @token_required
    def getdropoffs(current_user):
        data = request.get_json()

        store_id = data.get('store_id')

        dropoff_books = transactionModel.\
                        query.\
                        filter(transactionModel.store_id == store_id).\
                        filter( (transactionModel.transaction_status == transaction_statuses.uploaded_with_lender) | (transactionModel.transaction_status == transaction_statuses.return_by_borrower) ).\
                        all()

        if not dropoff_books: 
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
            t = [temp.details() for temp in dropoff_books]
            dropoff_book_list = []
            for book in dropoff_books:
                b = bookModel.query.filter_by(book_id = book.book_id).first()
                book_dict = b.details()
                book_dict['book_transaction_code'] = getcodes(book)
                dropoff_book_list.append(book_dict)

                return make_response( 
                                jsonify(
                                    {
                                        "message" : "All the books to be dropped off",
                                        "status" : True,
                                        "response" : {
                                            "dropoff_book_list" : dropoff_book_list,
                                            "test" : t
                                        }
                                    }
                                ),
                                200,
                            )
                        
                    
    @app.route('/Store/transaction/getallbooks', methods=['POST'])
    @token_required
    def getallbooks(current_user):
        data = request.get_json()

        store_id = data.get('store_id')

        books = transactionModel.\
                query.\
                filter(transactionModel.store_id == store_id).\
                filter( (transactionModel.transaction_status == transaction_statuses.submitted_by_lender) | (transactionModel.transaction_status == transaction_statuses.pickup_by_borrower) | (transactionModel.transaction_status == transaction_statuses.submitted_by_borrower) | (transactionModel.transaction_status == transaction_statuses.removed_by_lender)).\
                all()

        if not books: 
            return make_response( 
                                jsonify(
                                    {
                                        "message" : "No books at the store right now",
                                        "status" : True,
                                    }
                                ),
                                200,
                            )
        else :
            book_list = []
            for book in books:
                b = bookModel.query.filter_by(book_id = book.book_id).first()
                book_dict = b.details()
                book_dict['book_transaction_code'] = getcodes(book)
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
        



    @app.route('/',methods=['GET'])
    def hello():
        return jsonify({"hello": temp})



    return app



app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host='127.0.0.1',port=port,debug = True)