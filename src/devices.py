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

def toggle_device(mongo_client: MongoDbAccess, device):
    device_name = device[MongoDbAccess.DEVICE_NAME_FIELD]

    if MongoDbAccess.DEVICE_SWITCH_INTERVAL_FIELD not in device:
        interval = 300
    else:
        interval = device[MongoDbAccess.DEVICE_SWITCH_INTERVAL_FIELD]

    if MongoDbAccess.DEVICE_LAST_SWITCH_FIELD not in device:
        last_switch = datetime.datetime.min
    else:
        last_switch = device[MongoDbAccess.DEVICE_LAST_SWITCH_FIELD]

    current_time = datetime.datetime.now()

    if last_switch + datetime.timedelta(seconds=interval) > current_time:
        logging.info(f"too small interval for {device_name}, device interval is: {interval}")
        return
    
    last_switch = current_time

    mongo_client.update_device_switch_time(device_name=device_name, last_switch=last_switch)

    logging.info(f"last switch time updated for {device_name}")

    mqttmodule.send_device_toggle(device_name=device_name)

    logging.info(f"MQTT signal sent to {device_name}")

def device_state_machine():
    logging.info("entering devices state machine")
    with MongoDbAccess() as mongo_client:
        for device_group in mongo_client.get_devices_with_active_pair():
            device = device_group['device']
            device_name = device[MongoDbAccess.DEVICE_NAME_FIELD]
            is_dark = device[MongoDbAccess.DEVICE_IS_DARK_FIELD]
            is_power_on = device[MongoDbAccess.DEVICE_POWER_ON_FIELD]
            is_sleep = device[MongoDbAccess.DEVICE_IS_DEVICE_SLEEP]

            logging.info(f"states of {device_name}: dark - {is_dark}, powered - {is_power_on}, sleep - {is_sleep}")

            if is_dark:
                if is_power_on:
                    if is_sleep:
                        logging.info(f"device {device_name}: turning off, according to sleep mode, previously powered and darkness")
                        toggle_device(mongo_client=mongo_client, device=device)
                else:
                    if not is_sleep:
                        logging.info(f"device {device_name}: turning on, according to previously not powered and darkness")
                        toggle_device(mongo_client=mongo_client, device=device)
            else:
                if is_power_on:
                    logging.info(f"device {device_name}: turning off, according to previously powered and daylight")
                    toggle_device(mongo_client=mongo_client, device=device)

def device_connect_disconnect_handler(mobile_device_name: str, is_connected: bool):
    logging.info(f"updating mobile device ({mobile_device_name}) state (connected: {is_connected})")
    with MongoDbAccess() as mongo_client:
        mongo_client.update_mobile_device_stat(mobile_device_name, is_connected)
    logging.info("mobile devices states updated")
    device_state_machine()


def time_event_handler(event: DailyEvent):
    logging.info(f"updating devices state: {event}")
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
    logging.info(f"devices state update finished")
    device_state_machine()
