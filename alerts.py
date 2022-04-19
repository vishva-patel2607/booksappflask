import datetime
from os import sep
from models import transactionModel,bookModel,userModel
from status import Defaulttype, transaction_statuses

from app import create_app
from redisconnection import conn

app = create_app()
app.app_context().push()



def uploadedNotSubmitted():
    
    current_time = datetime.datetime.utcnow() - datetime.timedelta(weeks=1)

    one_week_ago = current_time 
    defaults = transactionModel.query.\
                filter(transactionModel.transaction_status.in_([transaction_statuses.lend.uploaded_with_lender,transaction_statuses.sell.uploaded_with_seller])).\
                filter(transactionModel.transaction_upload_ts < one_week_ago).\
                all()
    for default in defaults:
        conn.hset(default.lender_id,default.book_id,Defaulttype.UPLOADED_BOOK_NOT_SUBMITTED.name)

def returnedNotPickedup():
    current_time = datetime.datetime.utcnow() - datetime.timedelta(weeks=1)

    one_week_ago = current_time 
    defaults = transactionModel.query.\
                filter(transactionModel.transaction_status.in_([transaction_statuses.lend.submitted_by_borrower,transaction_statuses.lend.removed_by_lender,transaction_statuses.sell.removed_by_seller])).\
                filter(transactionModel.transaction_upload_ts < one_week_ago).\
                all()
    for default in defaults:
        conn.hset(default.lender_id,default.book_id,Defaulttype.UPLOADED_BOOK_NOT_SUBMITTED.name)

uploadedNotSubmitted()
        

