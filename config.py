class Config(object):
    DEBUG = False
    TESTING = False

    

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = "patel gang"
    SERVER_NAME = 'booksapp2021.herokuapp.com'
    PREFERRED_URL_SCHEME = 'https'
    pass

class TestingConfig(Config):
    TESTING = True
    pass