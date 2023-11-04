import pymongo
from env import Env
import datetime

class MongoDbAccess:

    DEVICE_NAME_FIELD = 'device_name'
    DEVICE_POWER_ON_FIELD = 'power_on'
    DEVICE_PAIRED_DEVICES_FIELD = 'paired_devices'
    DEVICE_LAST_SWITCH_FIELD = 'last_switch'
    DEVICE_SWITCH_INTERVAL_FIELD = 'switch_interval'
    DEVICE_IS_DARK_FIELD = 'device_in_dark'
    DEVICE_IS_DEVICE_SLEEP = 'device_sleep'

    MOBILE_DEVICE_NAME_FIELD = 'mobile_device_name'
    MOBILE_DEVICE_IP_ADDRESS = 'ip_address'
    MOBILE_DEVICE_IS_CONNECTED = 'is_connected'

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
    
    def __get_mobilde_devices_collection(self):
        db = self.__get_database()
        if db is None:
            return None
        collection_name = Env.get_mongo_mobile_devices_coll_name()
        if collection_name is None:
            return None
        return db[collection_name]

    def get_timings(self):
        devices_collection = self.__get_devices_collection()
        if devices_collection is None:
            return None
        return devices_collection.find({})
    
    def update_devices_sleep(self, is_in_sleep: bool):
        devices_collection = self.__get_devices_collection()
        devices_collection.update_many({},  {"$set": {self.DEVICE_IS_DEVICE_SLEEP: is_in_sleep}})

    def update_devices_dark(self, is_dark: bool):
        devices_collection = self.__get_devices_collection()
        devices_collection.update_many({},  {"$set": {self.DEVICE_IS_DARK_FIELD: is_dark}})
        
    def get_devices_names(self):
        devices_collection = self.__get_devices_collection()
        return devices_collection.find({}, {self.DEVICE_NAME_FIELD: 1})
    
    def get_devices(self):
        devices_collection = self.__get_devices_collection()
        return devices_collection.find({})
    
    def get_device_by_name(self, device_name: str):
        devices_collection = self.__get_devices_collection()
        return devices_collection.find_one({self.DEVICE_NAME_FIELD: device_name})
    
    def update_device_power_on(self, device_name: str, power_on: bool):
        devices_collection = self.__get_devices_collection()
        devices_collection.update_one({self.DEVICE_NAME_FIELD: device_name}, {"$set": {self.DEVICE_POWER_ON_FIELD: power_on}})
    
    def update_device_switch_time(self, device_name: str, last_switch: datetime.datetime):
        devices_collection = self.__get_devices_collection()
        devices_collection.update_one({self.DEVICE_NAME_FIELD: device_name}, {"$set": {self.DEVICE_LAST_SWITCH_FIELD: last_switch}})

    def update_mobile_device_stat(self, device_name: str, is_connected: bool):
        mobile_devices_connection = self.__get_mobilde_devices_collection()
        mobile_devices_connection.update_one({self.MOBILE_DEVICE_NAME_FIELD: device_name}, {"$set": {self.MOBILE_DEVICE_IS_CONNECTED: is_connected}})

    def get_paired_devices(self, mobile_device: str):
        devices_collection = self.__get_devices_collection()
        return devices_collection.find({"paired_devices": {"$in": [mobile_device]}})
    
    def get_devices_with_mobile_pair(self, is_active: bool):
        devices_collection = self.__get_devices_collection()

        if is_active:
            pipeline = [
                {
                    "$unwind": "$paired_devices"
                },
                {
                    "$lookup": {
                        "from": "mobile_devices",
                        "localField": "paired_devices",
                        "foreignField": "mobile_device_name",
                        "as": "mobile_device"
                    }
                },
                {
                    "$match": {
                        "mobile_device.is_connected": True
                    }
                },
                {
                    "$group": {
                        "_id": "$_id",
                        "device": {"$first": "$$ROOT"}
                    }
                }
            ]
        else:
            pipeline = [
                {
                    "$lookup": {
                        "from": "mobile_devices",
                        "localField": "paired_devices",
                        "foreignField": "mobile_device_name",
                        "as": "mobile_devices"
                    }
                },
                {
                    "$match": {
                        "mobile_devices.is_connected": False
                    }
                },
                {
                    "$project": {
                        "paired_devices": 1,
                        "mobile_devices": 1,
                        "mobile_devices_size": { "$size": "$mobile_devices" }
                    }
                },
                {
                    "$match": {
                        "$expr": { "$eq": ["$mobile_devices_size", { "$size": { "$filter": { "input": "$mobile_devices", "cond": { "$eq": ["$$this.is_connected", False] } } } }] }
                    }
                }
            ]
        return devices_collection.aggregate(pipeline)