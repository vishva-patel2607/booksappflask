from fileinput import filename
import requests
from models import booksubjectsModel, storeModel, transactionModel
from status import Transactiontype, transaction_statuses, store_transaction_statuses
import random
import math
import os
from InvoiceGenerator.api import Invoice, Item, Client, Provider, Creator
from InvoiceGenerator.pdf import SimpleInvoice
import datetime 
from s3_functions import upload_file, upload_invoice
from werkzeug.utils import secure_filename

def decode_redis(src):
    if isinstance(src, list):
        rv = list()
        for key in src:
            rv.append(decode_redis(key))
        return rv
    elif isinstance(src, dict):
        rv = dict()
        for key in src:
            rv[key.decode()] = decode_redis(src[key])
        return rv
    elif isinstance(src, bytes):
        return src.decode()
    else:
        raise Exception("type not handled: " +type(src))

def getpricing(transaction_type,book_price):
        if transaction_type == Transactiontype.lend.name:
            return int(0.15*book_price)
        elif transaction_type == Transactiontype.sell.name:
            return int(0.75*book_price)
        else:
            return "pricing error"

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

def generateBill(admin,store,transactions,invoice_data,access_key_id,access_key, bucket):
    os.environ["INVOICE_LANG"] = "en"

    client_details = "Store Name : " + store.store_name + "\n" + \
                    "Store Incharge : " + store.store_incharge + "\n" 
    
    # https://readthedocs.org/projects/invoicegenerator/downloads/pdf/latest/
    client = Client(client_details,
                    address = store.store_address,
                    zip_code = store.store_pincode
                    )
    # Bank Details left
    provider = Provider('BooksApp', 
                        address = 'address here',
                        zip_code = 'pincode here',
                        bank_account='bank account here',
                        bank_code='bank code here'
                        )
    
    creator = Creator(str(admin.firstname+" "+admin.lastname))
    invoice = Invoice(client, provider, creator)

    for transaction in transactions:
        invoice.add_item(Item(1, 
                            transaction.store_cost, 
                            description = str(transaction.transaction_id) + ' - ' + str(transaction.transaction_lenderpickup_ts) 
                        ))

    invoice.currency = "Rs."
    invoice.number = invoice_data.invoice_id
    docu = SimpleInvoice(invoice)
    time_now = datetime.datetime.now() 

    ### FILE NAME IN THIS FORMAT
    filename = secure_filename("invoice-"+str(store.store_id)+"-"+invoice_data.invoice_date.strftime("%m-%d-%Y_%H:%M:%S")+".pdf")
    ###


    doc_name = "static/tmp/"+filename
    docu.gen(doc_name, generate_qr_code=False)

    upload_invoice(access_key_id, access_key, bucket, filename, body=open(doc_name,'rb'))

    os.remove(doc_name)

    return filename

