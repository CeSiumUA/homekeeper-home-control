from logging import NOTSET
import logging
from log4mongo.handlers import MongoHandler
from helpers.env import Env

class MongoLogger(MongoHandler):
    def __init__(self):
        host = Env.get_mongo_connection_url()
        db_name = Env.get_mongo_logs_db_name()
        coll_name = Env.get_mongo_logs_coll_name()
        super().__init__(host=host, level=logging.INFO, database_name=db_name, collection=coll_name, capped=True, capped_size=10000000000)