import requests
from models import booksubjectsModel

def booksubjectAdd( book_id, isbn_no):
    response = (requests.get("https://openlibrary.org/isbn/" + isbn_no + ".json")).json()
    works = response.get('works')[0]
    response = (requests.get("https://openlibrary.org"+ works.get('key') +".json")).json()
    subjects = response.get('subjects')

    for sub in subjects:
        booksubjectsModel(book_id = book_id, book_subject = sub).insert()

    