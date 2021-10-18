class transaction_statuses:
    uploaded_with_lender = "Uploaded!, Please submit to shop"
    submitted_by_lender = "Book in shop"
    pickup_by_borrower = "Book will be picked up by someone!"
    borrowed_by_borrower = "Book is borrowed by someone!"
    return_by_borrower = "Book will be returned to shop shortly!"
    submitted_by_borrower = "Book returned! Please pick up book from shop"
    removed_by_lender = "Removed! Please pick up book from shop"
    pickup_by_lender = "Book with lender transaction complete"


class lender_transaction_statuses:
    pending = "Pending"
    removed_by_lender = "Removed by lender, Transaction finished"
    pickup_by_lender = "Received their share, Transaction finished"



class store_transaction_statuses:
    pending = "Pending"
    removed_by_lender = "Removed by lender, Transaction finished"
    dropoff_by_borrower = "Has lender and shop share"
    pickup_by_lender = "Received their share, Transaction finished"
    payment_collected = "Collected payment from shop"




class borrower_transaction_statuses:
    pending = "Pending"
    dropoff_by_borrower = "Received their share, Transaction finished"
    pickup_by_borrower = "Paid full book price"




