import os 

class BaseConfig(object):
    DEBUG = False
    TESTING = False
    AWS_ACCESS_KEY_ID=os.getenv('AWS_ACCESS_KEY_ID'),
    AWS_SECRET_ACCESS_KEY=os.getenv('AWS_SECRET_ACCESS_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAILER_ADDRESS = "booksapp2021@gmail.com"
    BUCKET = "booksapp-image-data"
    BOOK_UPLOAD_FOLDER = "uploads"
    BUCKET_LINK = "https://booksapp-image-data.s3.ap-south-1.amazonaws.com/book-image-folder/"
    FCM_ARN = "arn:aws:sns:ap-south-1:252518801138:app/GCM/booksapp-fcm"
    

class ProductionConfig(BaseConfig):
    SERVER_NAME = 'booksapp2021.herokuapp.com'
    PREFERRED_URL_SCHEME = 'https'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    REDISTOGO_URL = os.getenv('REDISTOGO_URL')
    SECRET_KEY = os.getenv('SECRET_KEY')


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "postgres://{}:{}@{}/{}".format('postgres', 'postgres', 'localhost:5432', 'booksapp')
    SECRET_KEY = "patel gang"

class TestingConfig(BaseConfig):
    TESTING = True


config = {
    "default": "config.BaseConfig",
    "development": "config.DevelopmentConfig",
    "production": "config.ProductionConfig",
}

def configure_app(app):
    config_name= os.getenv('FLASK_ENV')
    app.config.from_object(config[config_name])
    