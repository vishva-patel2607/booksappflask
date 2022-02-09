import os 

class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    AWS_ACCESS_KEY_ID=os.getenv('AWS_ACCESS_KEY_ID'),
    AWS_SECRET_ACCESS_KEY=os.getenv('AWS_SECRET_ACCESS_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAILER_ADDRESS = "booksapp2021@gmail.com"
    

class ProductionConfig(Config):
    SERVER_NAME = 'booksapp2021.herokuapp.com'
    PREFERRED_URL_SCHEME = 'https'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    REDISTOGO_URL = os.getenv('REDISTOGO_URL')


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "postgres://{}:{}@{}/{}".format('postgres', 'postgres', 'localhost:5432', 'booksapp')

class TestingConfig(Config):
    TESTING = True