import mqttmodule
import logging
from env import Env
from dbaccess import MongoDbAccess
import time
from apscheduler.schedulers.blocking import BlockingScheduler
import devicestat

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

    broker_host, broker_port, broker_username, broker_password = Env.get_mqtt_connection_params()
    if broker_host is None:
        logging.fatal("broker host is empty")

    mqttmodule.start_mqtt_client(broker_host=broker_host, broker_password=broker_password, broker_port=broker_port, broker_username=broker_username)

    scheduler = BlockingScheduler()

    with MongoDbAccess() as mongo_client:
        for device_set in mongo_client.get_devices():
            device_name = device_set[MongoDbAccess.DEVICE_NAME_FIELD]
            mqttmodule.subscribe_to_device(device_name=device_name)
            logging.info(f"subscribed to device: {device_name}")

    scheduler.add_job(devicestat.get_devices_stat, 'interval', minutes=20)

    try:
        logging.info("Scheduler started. Press Ctrl+C to exit.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler stopped.")