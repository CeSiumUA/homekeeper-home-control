import pymongo
from env import Env

class MongoDbAccess:

    DEVICE_NAME_FIELD = 'device_name'
    POWER_ON_FIELD = 'power_on'

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
    
    def __get_devices_collection(self):
        db = self.__get_database()
        if db is None:
            return None
        collection_name = Env.get_mongo_devices_coll_name()
        if collection_name is None:
            return None
        return db[collection_name]

    def get_timings(self):
        devices_collection = self.__get_devices_collection()
        if devices_collection is None:
            return None
        return devices_collection.find({})
    
    def update_bedtime(self, is_bed_time: bool):
        devices_collection = self.__get_devices_collection()
        
    def get_devices(self):
        devices_collection = self.__get_devices_collection()
        return devices_collection.find({}, {self.DEVICE_NAME_FIELD: 1})
    
    def update_device_stat(self, device_name: str, power_on: bool):
        devices_collection = self.__get_devices_collection()
        devices_collection.update_one({self.DEVICE_NAME_FIELD: device_name}, {"$set": {self.POWER_ON_FIELD: power_on}})