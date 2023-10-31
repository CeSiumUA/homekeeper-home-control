import pymongo
from env import Env

class MongoDbAccess:

    

    def __init__(self) -> None:
        self.__mongo_url = Env.get_mongo_connection_url()

    def __enter__(self):
        self.__client = pymongo.MongoClient(self.__mongo_url)
        return self

    def __exit__(self, *args):
        self.__client.close()

    def __get_database(self):
        db_name = Env.get_mongo_db_name()
        if db_name is None:
            return None
        return self.__client[db_name]
    
    def __get_states_collection(self):
        db = self.__get_database()
        if db is None:
            return None
        collection_name = Env.get_mongo_states_coll_name()
        if collection_name is None:
            return None
        return db[collection_name]

    def get_timings(self):
        states_collection = self.__get_states_collection()
        if states_collection is None:
            return None
        return states_collection.find({})
    
    def update_bedtime(self, is_bed_time: bool):
        states_collection = self.__get_states_collection()
        