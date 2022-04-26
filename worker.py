import os

import redis
from rq import Worker, Queue, Connection
from app import create_app
from redisconnection import conn







listen = ['High', 'Mid', 'Low']

app = create_app()
app.app_context().push()

if __name__ == '__main__':
    
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()