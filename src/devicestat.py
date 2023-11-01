from dbaccess import MongoDbAccess
import mqttmodule
import logging

def get_devices_stat():
    with MongoDbAccess() as mongo_client:
        for device_set in mongo_client.get_devices():
            device_name = device_set[MongoDbAccess.DEVICE_NAME_FIELD]
            mqttmodule.get_device_stat(device_name=device_name)