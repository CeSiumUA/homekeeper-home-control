from dbaccess import MongoDbAccess
import mqttmodule
import logging
from dailyevents import DailyEvent
import datetime


def get_devices_stat():
    logging.info('getting devices stat...')
    with MongoDbAccess() as mongo_client:
        for device_set in mongo_client.get_devices_names():
            device_name = device_set[MongoDbAccess.DEVICE_NAME_FIELD]
            logging.info(f'getting stat from: {device_name}')
            mqttmodule.get_device_stat(device_name=device_name)

def device_connect_disconnect_handler(mobile_device_name: str, is_connected: bool):
    with MongoDbAccess() as mongo_client:

        mongo_client.update_mobile_device_stat(mobile_device_name, is_connected)

        for device in mongo_client.get_paired_devices(mobile_device=mobile_device_name):
            switch_interval = device[MongoDbAccess.DEVICE_SWITCH_INTERVAL_FIELD]
            last_switch = device[MongoDbAccess.DEVICE_LAST_SWITCH_FIELD]
            is_device_powered = device[MongoDbAccess.DEVICE_POWER_ON_FIELD]
            is_device_dark = device[MongoDbAccess.DEVICE_IS_DARK_FIELD]

            if datetime.datetime.now() < last_switch + datetime.timedelta(minutes=switch_interval):
                continue
            elif is_connected and (is_device_powered or not is_device_dark):
                continue
            elif not is_connected and not is_device_powered:
                continue
            elif not is_connected and is_device_powered:
                # to be added
                pass
            elif is_connected and not is_device_powered and is_device_dark:
                # to be added
                pass


def time_event_handler(event: DailyEvent):
    # temporary
    if event == DailyEvent.CUSTOM_TIME:
        logging.info("there is still no handler for custom time.... need to think how it could be used in future...")
        return
    with MongoDbAccess() as mongo_client:
        if event == DailyEvent.BED_TIME or event == DailyEvent.WAKEUP_TIME:
            mongo_client.update_devices_sleep(True if event == DailyEvent.BED_TIME else False)
        elif event == DailyEvent.SUNRISE or event == DailyEvent.SUNSET:
            mongo_client.update_devices_dark(True if event == DailyEvent.SUNSET else False)
        else:
            logging.info(f"unknown event type: {event}")
            return
