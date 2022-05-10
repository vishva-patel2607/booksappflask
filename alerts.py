import datetime
from os import sep
from models import transactionModel,bookModel,userModel,db
from status import Defaulttype, Transactiontype, borrower_transaction_statuses, lender_transaction_statuses, store_transaction_statuses, transaction_statuses

from app import create_app
from redisconnection import conn
from utility import decode_redis

app = create_app()
app.app_context().push()



def uploadedNotSubmitted(initial_time):
    

    one_week_ago = initial_time - datetime.timedelta(weeks=1)
    defaults = transactionModel.query.\
                filter(transactionModel.transaction_status.in_([transaction_statuses.lend.uploaded_with_lender,transaction_statuses.sell.uploaded_with_seller])).\
                filter(transactionModel.transaction_upload_ts < one_week_ago).\
                all()
    for default in defaults:
        conn.hset(default.lender_id,default.book_id,Defaulttype.UPLOADED_BOOK_NOT_SUBMITTED.name)

def returnedNotPickedup(initial_time):

    one_week_ago = initial_time - datetime.timedelta(weeks=1)

    defaults = transactionModel.query.\
                filter(transactionModel.transaction_status.in_([transaction_statuses.lend.submitted_by_borrower,transaction_statuses.lend.removed_by_lender,transaction_statuses.sell.removed_by_seller])).\
                filter(transactionModel.transaction_return_ts < one_week_ago).\
                all()
    for default in defaults:
        conn.hset(default.lender_id,default.book_id,Defaulttype.RETURNED_BOOK_NOT_PICKEDUP.name)


def bookedNotPickedup(initial_time):

    one_week_ago = initial_time - datetime.timedelta(weeks=1)

    two_week_ago = initial_time - datetime.timedelta(weeks=2)

    default1 = transactionModel.query.\
                filter(transactionModel.transaction_status.in_([transaction_statuses.lend.pickup_by_borrower,transaction_statuses.sell.booked_by_buyer])).\
                filter(transactionModel.transaction_book_ts < one_week_ago).\
                filter(transactionModel.transaction_book_ts > two_week_ago).\
                all()

    for default in default1:
        conn.hset(default.borrower_id,default.book_id,Defaulttype.BOOKED_BOOK_NOT_PICKEDUP.name)

    default2 = transactionModel.query.\
                filter(transactionModel.transaction_status.in_([transaction_statuses.lend.pickup_by_borrower,transaction_statuses.sell.booked_by_buyer])).\
                filter(transactionModel.transaction_book_ts > two_week_ago).\
                all()

    for default in default2:
        if default.transaction_type == Transactiontype.lend.name:
            default.transaction_status = transaction_statuses.lend.submitted_by_lender
            default.borrower_id = None
            default.transaction_book_ts = None
            default.update()
        else:
            default.transaction_status = transaction_statuses.sell.submitted_by_seller
            default.borrower_id = None
            default.transaction_book_ts = None
            default.update()


def borrowedNeverReturned(initial_time):
    
    three_week_ago = initial_time - datetime.timedelta(weeks=3)

    four_week_ago = initial_time - datetime.timedelta(weeks=4)

    five_week_ago = initial_time - datetime.timedelta(weeks=5)

    six_week_ago = initial_time - datetime.timedelta(weeks=6)

    nine_week_ago = initial_time - datetime.timedelta(weeks=9)

    default1 = db.session.query(userModel,transactionModel).\
                filter(transactionModel.transaction_status == transaction_statuses.lend.borrowed_by_borrower).\
                filter(transactionModel.transaction_pickup_ts < three_week_ago).\
                filter(transactionModel.transaction_pickup_ts > four_week_ago).\
                filter(userModel.usernumber == transactionModel.borrower_id).\
                all()

    for user,default in default1:
        default.transaction_score = 90
        default.setpricing(default.transaction_type,transaction_score=90,userscore = user.userscore)
        default.update()
        conn.hset(default.borrower_id,default.book_id,Defaulttype.BORROWED_BOOK_NOT_RETURNED.name)

    default2 = db.session.query(userModel,transactionModel).\
                filter(transactionModel.transaction_status == transaction_statuses.lend.borrowed_by_borrower).\
                filter(transactionModel.transaction_pickup_ts < four_week_ago).\
                filter(transactionModel.transaction_pickup_ts > five_week_ago).\
                filter(userModel.usernumber == transactionModel.borrower_id).\
                all()

    for user,default in default2:
        default.transaction_score = 80
        default.setpricing(default.transaction_type,transaction_score=80,userscore = user.userscore)
        default.update()

    default3 = db.session.query(userModel,transactionModel).\
                filter(transactionModel.transaction_status == transaction_statuses.lend.borrowed_by_borrower).\
                filter(transactionModel.transaction_pickup_ts < five_week_ago).\
                filter(transactionModel.transaction_pickup_ts > six_week_ago).\
                filter(userModel.usernumber == transactionModel.borrower_id).\
                all()

    for user,default in default3:
        default.transaction_score = 70
        default.setpricing(default.transaction_type,transaction_score=70,userscore = user.userscore)
        default.update()


    default4 = transactionModel.query.\
                filter(transactionModel.transaction_status == transaction_statuses.lend.borrowed_by_borrower).\
                filter(transactionModel.transaction_pickup_ts < six_week_ago).\
                filter(transactionModel.transaction_pickup_ts > nine_week_ago).\
                all()

    for default in default4:
        default.transaction_score = 50
        default.update()
        conn.hset(default.borrower_id,default.book_id,Defaulttype.BOOK_BORROWED_MAYBE_LOST.name)



    default5 = transactionModel.query.\
                filter(transactionModel.transaction_status == transaction_statuses.lend.borrowed_by_borrower).\
                filter(transactionModel.transaction_pickup_ts < nine_week_ago).\
                all()

    for default in default5:
        default.transaction_score = 25
        default.transaction_status = transaction_statuses.lend.lost_by_borrower
        default.update()
        if conn.hexists(default.borrower_id,default.book_id):
            conn.hdel(default.borrower_id,default.book_id)
        


    
def removedNeverDroppedoff(initial_time):
    one_week_ago = initial_time - datetime.timedelta(weeks=1)

    two_week_ago = initial_time - datetime.timedelta(weeks=2)

    three_week_ago = initial_time - datetime.timedelta(weeks=3)

    four_week_ago = initial_time - datetime.timedelta(weeks=4)

    five_week_ago = initial_time - datetime.timedelta(weeks=5)

    six_week_ago = initial_time - datetime.timedelta(weeks=6)

    nine_week_ago = initial_time - datetime.timedelta(weeks=9)

    default1 = db.session.query(userModel,transactionModel).\
                filter(transactionModel.transaction_status == transaction_statuses.lend.return_by_borrower).\
                filter(transactionModel.transaction_remove_ts < one_week_ago).\
                filter(transactionModel.transaction_pickup_ts < three_week_ago).\
                filter(transactionModel.transaction_pickup_ts > four_week_ago).\
                filter(userModel.usernumber == transactionModel.borrower_id).\
                all()

    for user,default in default1:
        default.transaction_score = 90
        default.setpricing(default.transaction_type,transaction_score=90,userscore = user.userscore)
        default.update()
        conn.hset(default.borrower_id,default.book_id,Defaulttype.REMOVED_BOOK_NOT_DROPPEDOFF.name)

    default2 = db.session.query(userModel,transactionModel).\
                filter(transactionModel.transaction_status == transaction_statuses.lend.return_by_borrower).\
                filter(transactionModel.transaction_remove_ts < one_week_ago).\
                filter(transactionModel.transaction_pickup_ts < four_week_ago).\
                filter(transactionModel.transaction_pickup_ts > five_week_ago).\
                filter(userModel.usernumber == transactionModel.borrower_id).\
                all()

    for user,default in default2:
        default.transaction_score = 80
        default.setpricing(default.transaction_type,transaction_score=80,userscore = user.userscore)
        default.update()

    
    default3 =  db.session.query(userModel,transactionModel).\
                filter(transactionModel.transaction_status == transaction_statuses.lend.return_by_borrower).\
                filter(transactionModel.transaction_remove_ts < one_week_ago).\
                filter(transactionModel.transaction_pickup_ts < five_week_ago).\
                filter(transactionModel.transaction_pickup_ts > six_week_ago).\
                filter(userModel.usernumber == transactionModel.borrower_id).\
                all()

    for default in default3:
        default.transaction_score = 70
        default.setpricing(default.transaction_type,transaction_score=70,userscore = user.userscore)
        default.update()

    default4 = transactionModel.query.\
                filter(transactionModel.transaction_status == transaction_statuses.lend.return_by_borrower).\
                filter(transactionModel.transaction_remove_ts < one_week_ago).\
                filter(transactionModel.transaction_pickup_ts < six_week_ago).\
                filter(transactionModel.transaction_pickup_ts > nine_week_ago).\
                all()

    for default in default4:
        default.transaction_score = 50
        default.update()
        conn.hset(default.borrower_id,default.book_id,Defaulttype.BOOK_BORROWED_MAYBE_LOST.name)


    default5 = transactionModel.query.\
                filter(transactionModel.transaction_status == transaction_statuses.lend.return_by_borrower).\
                filter(transactionModel.transaction_remove_ts < one_week_ago).\
                filter(transactionModel.transaction_pickup_ts < nine_week_ago).\
                all()

    for default in default5:
        default.transaction_score = 25
        default.transaction_status = transaction_statuses.lend.lost_by_borrower
        default.update()
        if conn.hexists(default.borrower_id,default.book_id):
            conn.hdel(default.borrower_id,default.book_id)

    
    
def testJobber():
    initial_time = datetime.datetime.utcnow()
    one_week_ago = initial_time - datetime.timedelta(weeks=1,days=1)

    two_week_ago = initial_time - datetime.timedelta(weeks=2,days=1)

    three_week_ago = initial_time - datetime.timedelta(weeks=3,days=1)

    four_week_ago = initial_time - datetime.timedelta(weeks=4,days=1)

    five_week_ago = initial_time - datetime.timedelta(weeks=5,days=1)

    six_week_ago = initial_time - datetime.timedelta(weeks=6,days=1)

    nine_week_ago = initial_time - datetime.timedelta(weeks=9,days=1)

    raj_id = 14
    vishva_id = 13
    store_id = 4
    book_img_url = 'https://booksapp-image-data.s3.ap-south-1.amazonaws.com/book-image-folder/book-01-23-2022_151001.jpg'

    '''
    ################# DEFAULT 1##########################################
    book = bookModel(
                book_name  = 'default 1',
                book_year = 1977,
                book_condition = 'good',
                book_img = book_img_url,
                book_price = 500,
                store_id = store_id,
                usernumber = raj_id,
                book_author = 'Vishva Patel',
                book_isbn= '9780099590088',
                book_category='romance'
            )

    book.insert()

    transaction = transactionModel(
        book_id= book.book_id,
        transaction_status= transaction_statuses.lend.uploaded_with_lender,
        lender_id= raj_id,
        store_id= store_id,
        borrower_id= None,
        invoice_id = None,
        lender_transaction_status= lender_transaction_statuses.lend.pending,
        store_transaction_status= store_transaction_statuses.lend.pending,
        borrower_transaction_status = borrower_transaction_statuses.lend.pending,
        book_price= 500,
        transaction_upload_ts= one_week_ago,
        transaction_submit_ts= None,
        transaction_book_ts= None,
        transaction_pickup_ts= None,
        transaction_remove_ts = None,
        transaction_return_ts= None,
        transaction_lenderpickup_ts= None,
        transaction_type=Transactiontype.lend.name
    )

    transaction.insert()
    '''



    ################################### DEFAULT 2 #######################################
    '''
    book = bookModel(
                book_name  = 'default 2',
                book_year = 1977,
                book_condition = 'good',
                book_img = book_img_url,
                book_price = 500,
                store_id = store_id,
                usernumber = raj_id,
                book_author = 'Vishva Patel',
                book_isbn= '9780099590088',
                book_category='romance'
            )

    book.insert()

    transaction = transactionModel(
        book_id= book.book_id,
        transaction_status= transaction_statuses.lend.removed_by_lender,
        lender_id= raj_id,
        store_id= store_id,
        borrower_id= None,
        invoice_id = None,
        lender_transaction_status= lender_transaction_statuses.lend.removed_by_lender,
        store_transaction_status= store_transaction_statuses.lend.removed_by_lender,
        borrower_transaction_status = borrower_transaction_statuses.lend.pending,
        book_price= 500,
        transaction_upload_ts= two_week_ago,
        transaction_submit_ts= None,
        transaction_book_ts= None,
        transaction_pickup_ts= None,
        transaction_remove_ts = None,
        transaction_return_ts= one_week_ago,
        transaction_lenderpickup_ts= None,
        transaction_type=Transactiontype.lend.name
    )

    transaction.insert()

    '''
    ################################### DEFAULT 3 #######################################

    '''book = bookModel(
                book_name  = 'default 3',
                book_year = 1977,
                book_condition = 'good',
                book_img = book_img_url,
                book_price = 500,
                store_id = store_id,
                usernumber = vishva_id,
                book_author = 'Vishva Patel',
                book_isbn= '9780099590088',
                book_category='romance'
            )

    book.insert()

    transaction = transactionModel(
        book_id= book.book_id,
        transaction_status= transaction_statuses.lend.pickup_by_borrower,
        lender_id= vishva_id,
        store_id= store_id,
        borrower_id= raj_id,
        invoice_id = None,
        lender_transaction_status= lender_transaction_statuses.lend.pending,
        store_transaction_status= store_transaction_statuses.lend.pending,
        borrower_transaction_status = borrower_transaction_statuses.lend.pending,
        book_price= 500,
        transaction_upload_ts= two_week_ago,
        transaction_submit_ts= two_week_ago,
        transaction_book_ts= one_week_ago,
        transaction_pickup_ts= None,
        transaction_remove_ts = None,
        transaction_return_ts= None,
        transaction_lenderpickup_ts= None,
        transaction_type=Transactiontype.lend.name
    )

    transaction.insert()
    '''


    ################################### DEFAULT 4 #######################################
    '''
    book = bookModel(
                book_name  = 'default 4',
                book_year = 1977,
                book_condition = 'good',
                book_img = book_img_url,
                book_price = 500,
                store_id = store_id,
                usernumber = vishva_id,
                book_author = 'Vishva Patel',
                book_isbn= '9780099590088',
                book_category='romance'
            )

    book.insert()

    transaction = transactionModel(
        book_id= book.book_id,
        transaction_status= transaction_statuses.lend.borrowed_by_borrower,
        lender_id= vishva_id,
        store_id= store_id,
        borrower_id= raj_id,
        invoice_id = None,
        lender_transaction_status= lender_transaction_statuses.lend.pending,
        store_transaction_status= store_transaction_statuses.lend.pending,
        borrower_transaction_status = borrower_transaction_statuses.lend.pickup_by_borrower,
        book_price= 500,
        transaction_upload_ts= two_week_ago,
        transaction_submit_ts= two_week_ago,
        transaction_book_ts= three_week_ago,
        transaction_pickup_ts= three_week_ago,
        transaction_remove_ts = None,
        transaction_return_ts= None,
        transaction_lenderpickup_ts= None,
        transaction_type=Transactiontype.lend.name
    )

    transaction.insert()
    '''
    ################################### DEFAULT 5 #######################################

    book = bookModel(
                book_name  = 'default 5',
                book_year = 1977,
                book_condition = 'good',
                book_img = book_img_url,
                book_price = 500,
                store_id = store_id,
                usernumber = vishva_id,
                book_author = 'Vishva Patel',
                book_isbn= '9780099590088',
                book_category='romance'
            )

    book.insert()

    transaction = transactionModel(
        book_id= book.book_id,
        transaction_status= transaction_statuses.lend.return_by_borrower,
        lender_id= vishva_id,
        store_id= store_id,
        borrower_id= raj_id,
        invoice_id = None,
        lender_transaction_status= lender_transaction_statuses.lend.pending,
        store_transaction_status= store_transaction_statuses.lend.pending,
        borrower_transaction_status = borrower_transaction_statuses.lend.pickup_by_borrower,
        book_price= 500,
        transaction_upload_ts= two_week_ago,
        transaction_submit_ts= two_week_ago,
        transaction_book_ts= three_week_ago,
        transaction_pickup_ts= three_week_ago,
        transaction_remove_ts = one_week_ago,
        transaction_return_ts= None,
        transaction_lenderpickup_ts= None,
        transaction_type=Transactiontype.lend.name
    )

    transaction.insert()


    print("\n\n\nTEST JOBBER DONE ------------------------->\n\n\n")




def regularJob():
    initial_time = datetime.datetime.utcnow()
    uploadedNotSubmitted(initial_time)
    print("uploadedNotSubmitted COMPLETED ----------------------->")
    returnedNotPickedup(initial_time)
    print("returnedNotPickedup COMPLETED ----------------------->")
    bookedNotPickedup(initial_time)
    print("bookedNotPickedup COMPLETED ----------------------->")
    borrowedNeverReturned(initial_time)
    print("borrowedNeverReturned COMPLETED ----------------------->")
    removedNeverDroppedoff(initial_time)
    print("removedNeverDroppedoff COMPLETED ----------------------->")
    print("\n\n\n COMPLETED ----------------------->")


def testJobberCheck():
    data = conn.hgetall(14)

    if data is not None and len(data) > 0:
        decoded_data = decode_redis(data)
        print("\n\n\nTHE CACHED DEFAULT DATA IS ------------------------->\n\n\n")
        print(decoded_data)


testJobber()      
regularJob()
testJobberCheck()
