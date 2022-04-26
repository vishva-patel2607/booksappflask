import datetime
from os import sep
from models import transactionModel,bookModel,userModel,db
from status import Defaulttype, Transactiontype, transaction_statuses

from app import create_app
from redisconnection import conn

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
                filter(transactionModel.transaction_upload_ts < one_week_ago).\
                all()
    for default in defaults:
        conn.hset(default.lender_id,default.book_id,Defaulttype.UPLOADED_BOOK_NOT_SUBMITTED.name)


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
            conn.hdel(default.lender_id,default.book_id)
        


    
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
            conn.hdel(default.lender_id,default.book_id)

    
    

def regularJob():
    uploadedNotSubmitted()
    print("uploadedNotSubmitted COMPLETED ----------------------->")
    returnedNotPickedup()
    print("returnedNotPickedup COMPLETED ----------------------->")
    bookedNotPickedup()
    print("bookedNotPickedup COMPLETED ----------------------->")
    borrowedNeverReturned()
    print("borrowedNeverReturned COMPLETED ----------------------->")
    removedNeverDroppedoff()
    print("removedNeverDroppedoff COMPLETED ----------------------->")
    print("\n\n\n COMPLETED ----------------------->")
        
regularJob()
