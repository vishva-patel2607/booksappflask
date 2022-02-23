import requests
from models import booksubjectsModel, storeModel, transactionModel
from status import transaction_statuses, store_transaction_statuses
import random
import math
import os
from InvoiceGenerator.api import Invoice, Item, Client, Provider, Creator
from InvoiceGenerator.pdf import SimpleInvoice
import datetime 

def booksubjectAdd( book_id, isbn_no):
    response = (requests.get("https://openlibrary.org/isbn/" + isbn_no + ".json")).json()
    works = response.get('works')[0]
    response = (requests.get("https://openlibrary.org"+ works.get('key') +".json")).json()
    subjects = response.get('subjects')

    for sub in subjects:
        booksubjectsModel(book_id = book_id, book_subject = sub).insert()



def generateOTP():
    digits = "0123456789"
    OTP = ""
    for i in range(6) :
        OTP += digits[math.floor(random.random() * 10)]
 
    return OTP

def generateBill(storeId = None):
    os.environ["INVOICE_LANG"] = "en"
    '''
    lis1 = transactionModel.query.\
            filter(transactionModel.store_id == storeId).\
            filter(transactionModel.transaction_status == transaction_statuses.pickup_by_lender).\
            filter(transactionModel.store_transaction_status == store_transaction_statuses.pickup_by_lender).\
            all()

    store_details = storeModel.query.\
            filter(storeModel.store_id == storeId).\
            first()
    '''

    # test cases
    store_details = {
        'store_name' : "Test abc",
        'store_incharge' : "xyz",
        'store_id' : 0000,
        'store_address' : "TEST ADDRESS",
        'store_pincode' : "3800000"
    }
    lis1 = [
        {
            'store_cost' : 10,
            'transaction_id' : 000000,
            'transaction_lenderpickup_ts' : "ABC DAY"
        },
        {
            'store_cost' : 20,
            'transaction_id' : 100000,
            'transaction_lenderpickup_ts' : "ABC2 DAY"
        }
    ]

    client_details = "Store Name : " + store_details.get('store_name') + "\n" + \
                    "Store Incharge : " + store_details.get('store_incharge') + "\n" 
    
    # https://readthedocs.org/projects/invoicegenerator/downloads/pdf/latest/
    client = Client(client_details,
                    address = store_details.get('store_address'),
                    zip_code = store_details.get('store_pincode')
                    )
    # Bank Details left
    provider = Provider('BooksApp', 
                        address = 'address here',
                        zip_code = 'pincode here',
                        bank_account='bank account here',
                        bank_code='bank code here'
                        )
    
    creator = Creator('BooksApp')
    invoice = Invoice(client, provider, creator)

    for cust in lis1:
        invoice.add_item(Item(1, 
                            cust.get('store_cost'), 
                            description = str(cust.get('transaction_id')) + ' - ' + str(cust.get('transaction_lenderpickup_ts')) 
                        ))

    invoice.currency = "Rs."
    # invoice number left
    invoice.number = store_details.get('store_id')
    docu = SimpleInvoice(invoice)
    time_now = datetime.datetime.now() 
    date = str(time_now.year) + str(time_now.month) + str(time_now.day) + str(time_now.hour) + str(time_now.min)
    doc_name = str(store_details.get('store_id')) + "-" + date
    docu.gen(doc_name + ".pdf", generate_qr_code=False)

generateBill()