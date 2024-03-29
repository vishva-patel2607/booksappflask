from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from app import app
from models import db,userModel,bookModel,storeModel,transactionModel
from geoalchemy2.types import Geometry

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)
if __name__ == '__main__':
    manager.run()