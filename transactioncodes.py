from status import transaction_statuses
from datetime import datetime

def getcodes(transaction):
    code = str()
    tran_id = str(transaction.transaction_id).rjust(7,"0")
    if transaction.transaction_status == transaction_statuses.uploaded_with_lender:
        code = transaction.transaction_upload_ts.strftime("%m%d%Y%H%M%S")+tran_id
    elif transaction.transaction_status == transaction_statuses.submitted_by_lender or transaction.transaction_status == transaction_statuses.pickup_by_borrower:
        code = transaction.transaction_submit_ts.strftime("%m%d%Y%H%M%S")+tran_id
    elif transaction.transaction_status == transaction_statuses.borrowed_by_borrower or transaction.transaction_status == transaction_statuses.return_by_borrower or transaction.transaction_status == transaction_statuses.submitted_by_borrower:
        code = transaction.transaction_pickup_ts.strftime("%m%d%Y%H%M%S")+tran_id
    elif transaction.transaction_status == transaction_statuses.removed_by_lender:
        code = transaction.transaction_return_ts.strftime("%m%d%Y%H%M%S")+tran_id
    else :
        code = transaction.transaction_lenderpickup_ts.strftime("%m%d%Y%H%M%S")+tran_id

    return code

