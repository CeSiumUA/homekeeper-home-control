import mqttmodule
import logging
from env import Env
from dbaccess import MongoDbAccess
import time

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

    broker_host, broker_port, broker_username, broker_password = Env.get_mqtt_connection_params()
    if broker_host is None:
        logging.fatal("broker host is empty")

    mqttmodule.start_mqtt_client(broker_host=broker_host, broker_password=broker_password, broker_port=broker_port, broker_username=broker_username)

    with MongoDbAccess() as mongo_client:
        for device_set in mongo_client.get_devices():
            mqttmodule.subscribe_to_device(device_name=device_set['device_name'])