import mqttmodule
import logging
from env import Env

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

broker_host, broker_port, broker_username, broker_password = Env.get_mqtt_connection_params()
if broker_host is None:
    logging.fatal("broker host is empty")

mongo_url = Env.get_mongo_connection_url()
if mongo_url is None:
    logging.fatal("mongo url is empty")

mqttmodule.start_mqtt_client(broker_host=broker_host, broker_password=broker_password, broker_port=broker_port, broker_username=broker_username)