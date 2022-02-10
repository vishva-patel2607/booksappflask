import os

import redis
from rq import Worker, Queue, Connection
from app import app
from redisconnection import conn







listen = ['mail', 's3', 'notification']


app.app_context().push()

if __name__ == '__main__':
    
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()