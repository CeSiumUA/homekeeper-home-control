from enum import Enum
import pymongo
from helpers.env import Env
import datetime

class DeviceType(Enum):
    DESK_LIGHT = 'desk_light'
    FLOOR_HEATING = 'floor_heating'

class MongoDbAccess(pymongo.MongoClient):

    DEVICE_NAME_FIELD = 'device_name'
    DEVICE_POWER_ON_FIELD = 'power_on'
    DEVICE_PAIRED_DEVICES_FIELD = 'paired_devices'
    DEVICE_LAST_SWITCH_FIELD = 'last_switch'
    DEVICE_SWITCH_INTERVAL_FIELD = 'switch_interval'
    DEVICE_IS_DARK_FIELD = 'device_in_dark'
    DEVICE_IS_DEVICE_SLEEP = 'device_sleep'
    DEVICE_TEMPERATURE_FIELD = 'device_temperature'
    DEVICE_TYPE_FIELD = 'device_type'
    DEVICE_TOTAL_ENERGY_FIELD = 'device_total_energy'
    DEVICE_IS_POWER_FORCED_FIELD = 'device_is_power_forced'

    MOBILE_DEVICE_NAME_FIELD = 'mobile_device_name'
    MOBILE_DEVICE_IP_ADDRESS = 'ip_address'
    MOBILE_DEVICE_IS_CONNECTED = 'is_connected'

    def __init__(self) -> None:
        mongo_url = Env.get_mongo_connection_url()
        super().__init__(mongo_url)

    def __enter__(self):
        super().__enter__()
        return self

    def __get_database(self):
        db_name = Env.get_mongo_db_name()
        if db_name is None:
            return None
        return self[db_name]
    
    def __get_devices_collection(self):
        db = self.__get_database()
        if db is None:
            return None
        collection_name = Env.get_mongo_devices_coll_name()
        if collection_name is None:
            return None
        return db[collection_name]
    
    def __get_mobile_devices_collection(self):
        db = self.__get_database()
        if db is None:
            return None
        collection_name = Env.get_mongo_mobile_devices_coll_name()
        if collection_name is None:
            return None
        return db[collection_name]
    
    def __get_schedules_collection(self):
        db = self.__get_database()
        if db is None:
            return None
        collection_name = Env.get_mongo_schedules_coll_name()
        if collection_name is None:
            return None
        return db[collection_name]

    def get_timings(self):
        schedules_collection = self.__get_schedules_collection()
        if schedules_collection is None:
            return None
        return schedules_collection.find({})
    
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
    
    def update_device_sensor_stats(self, device_name: str, device_sensor_stats):
        devices_collection = self.__get_devices_collection()
        devices_collection.update_one({self.DEVICE_NAME_FIELD: device_name}, {"$set": device_sensor_stats})

    def update_device_forced_state(self, device_name: str, is_forced: bool):
        devices_collection = self.__get_devices_collection()
        devices_collection.update_one({self.DEVICE_NAME_FIELD: device_name}, {"$set": {self.DEVICE_IS_POWER_FORCED_FIELD: is_forced}})

    def update_device_stats(self, device_name: str, last_switch: datetime.datetime, forced_power: bool):

        stats = {
            MongoDbAccess.DEVICE_LAST_SWITCH_FIELD: last_switch,
            MongoDbAccess.DEVICE_IS_POWER_FORCED_FIELD: forced_power
        }

        devices_collection = self.__get_devices_collection()
        devices_collection.update_one({self.DEVICE_NAME_FIELD: device_name}, {"$set": stats})

    def update_mobile_device_stat(self, device_name: str, is_connected: bool):
        mobile_devices_connection = self.__get_mobile_devices_collection()
        mobile_devices_connection.update_one({self.MOBILE_DEVICE_NAME_FIELD: device_name}, {"$set": {self.MOBILE_DEVICE_IS_CONNECTED: is_connected}})

    def get_paired_devices(self, mobile_devices):
        devices_collection = self.__get_devices_collection()

        return devices_collection.find({"paired_devices": {"$in": mobile_devices}})
    
    def get_offline_mobile_devices(self):
        mobile_devices_collection = self.__get_mobile_devices_collection()
        return mobile_devices_collection.find({"is_connected": False})
    
    def get_mobile_devices(self):
        mobile_devices_collection = self.__get_mobile_devices_collection()
        return mobile_devices_collection.find({})
    
    def get_devices_with_mobile_pair(self):
        devices_collection = self.__get_devices_collection()

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
        return devices_collection.aggregate(pipeline)