import enum


class Usertype (enum.Enum):
    user = 1
    store = 2
    admin = 3

class Transactiontype (enum.Enum):
    lend = 1
    sell = 2
    
class transaction_statuses:
    class lend:
        uploaded_with_lender = "Uploaded!, Please submit to shop"
        submitted_by_lender = "Book in shop"
        pickup_by_borrower = "Book will be picked up by someone!"
        borrowed_by_borrower = "Book is borrowed by someone!"
        return_by_borrower = "Book will be returned to shop shortly!"
        submitted_by_borrower = "Book returned! Please pick up book from shop"
        removed_by_lender = "Removed! Please pick up book from shop"
        pickup_by_lender = "Book with lender transaction complete"
    class sell:
        uploaded_with_seller = "Uploaded! Please submit to shop"
        submitted_by_seller = "Book in shop"
        booked_by_buyer = "Book will be bought by someone!"
        pickup_by_buyer = "Book sold! Collect your share from shop"
        collected_by_seller = "Share collected successfully transaction complete"
        #cancellation cases
        removed_by_seller = "Removed! Please pick up book from shop"
        pickup_by_seller = "Book with lender transaction complete"


class lender_transaction_statuses:
    class lend:
        pending = "Pending"
        removed_by_lender = "Removed by lender, Transaction finished"
        pickup_by_lender = "Received their share, Transaction finished"
    class buy:
        pending = "Pending"
        removed_by_seller = "Removed by seller, Transaction finished"
        collected_by_seller = "Received their share, Transaction finished"



class store_transaction_statuses:
    class lend:
        pending = "Pending"
        removed_by_lender = "Removed by lender, Transaction finished"
        dropoff_by_borrower = "Has lender and shop share"
        pickup_by_lender = "Received their share, Transaction finished"
        transaction_invoiced = "Transaction Invoiced"
        payment_collected = "Collected payment from shop"
    class sell:
        pending = "Pending"
        removed_by_seller = "Removed by seller, Transaction finished"
        pickup_by_buyer = "Has seller and shop share"
        collected_by_seller = "Received their share, Transaction finished"
        transaction_invoiced = "Transaction Invoiced"
        payment_collected = "Collected payment from shop"






class borrower_transaction_statuses:
    class lend:
        pending = "Pending"
        dropoff_by_borrower = "Received their share, Transaction finished"
        pickup_by_borrower = "Paid full book price"
    class sell:
        pending = "Pending"
        pickup_by_borrower = "Received their book, Transaction finished"
        


class invoice_statuses:
    pending = "Pending"
    paid = "Paid"




