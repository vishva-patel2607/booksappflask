import requests
from models import booksubjectsModel
import random
import math

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