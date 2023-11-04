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

def toggle_device(mongo_client: MongoDbAccess, device, state: bool):
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

    mqttmodule.send_device_toggle(device_name=device_name, state=state)

    logging.info(f"MQTT signal sent to {device_name}")

def process_device_states(get_active_devices: bool = True):
    with MongoDbAccess() as mongo_client:
        if get_active_devices:
            for device_group in mongo_client.get_devices_with_mobile_pair():
                device = device_group['device']
                device_state_machine(mongo_client=mongo_client, device=device)
        else:
            offline_mobile_devices = list(mongo_client.get_offline_mobile_devices())
            projected_offline_devices = [md[MongoDbAccess.MOBILE_DEVICE_NAME_FIELD] for md in offline_mobile_devices]
            logging.info(f"got offline devices: {projected_offline_devices}")
            for device in mongo_client.get_paired_devices(projected_offline_devices):
                logging.info(f"processing device: {device}")
                device_mobile_devices = device[MongoDbAccess.DEVICE_PAIRED_DEVICES_FIELD]
                are_all_mobile_devices_offline = all(md in projected_offline_devices for md in device_mobile_devices)
                if are_all_mobile_devices_offline:
                    device_state_machine(mongo_client=mongo_client, device=device, forced_shutdown=True)
                else:
                    logging.info("device has still some mobiles connected to network")


def device_state_machine(mongo_client, device, forced_shutdown: bool = False):
    logging.info("entering devices state machine")
    device_name = device[MongoDbAccess.DEVICE_NAME_FIELD]
    is_dark = device[MongoDbAccess.DEVICE_IS_DARK_FIELD]
    is_power_on = device[MongoDbAccess.DEVICE_POWER_ON_FIELD]
    is_sleep = device[MongoDbAccess.DEVICE_IS_DEVICE_SLEEP]

    logging.info(f"states of {device_name}: dark - {is_dark}, powered - {is_power_on}, sleep - {is_sleep}")

    if forced_shutdown:
        logging.info(f"forcing {device_name} to power off")
        toggle_device(mongo_client=mongo_client, device=device, state=False)
        return

    if is_dark:
        if is_power_on:
            if is_sleep:
                logging.info(f"device {device_name}: turning off, according to sleep mode, previously powered and darkness")
                toggle_device(mongo_client=mongo_client, device=device, state=False)
        else:
            if not is_sleep:
                logging.info(f"device {device_name}: turning on, according to previously not powered and darkness")
                toggle_device(mongo_client=mongo_client, device=device, state=True)
    else:
        if is_power_on:
            logging.info(f"device {device_name}: turning off, according to previously powered and daylight")
            toggle_device(mongo_client=mongo_client, device=device, state=False)

def device_connect_disconnect_handler(mobile_device_name: str, is_connected: bool):
    logging.info(f"updating mobile device ({mobile_device_name}) state (connected: {is_connected})")
    with MongoDbAccess() as mongo_client:
        mongo_client.update_mobile_device_stat(mobile_device_name, is_connected)
    logging.info("mobile devices states updated")
    process_device_states(is_connected)

def device_direct_command_handler(device_name: str, state: bool):
    with MongoDbAccess() as mongo_client:
        device = mongo_client.get_device_by_name(device_name=device_name)
        if device is None:
            logging.info(f"device {device_name} not found")
            return
        toggle_device(mongo_client=mongo_client, state=state, device=device)

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
    process_device_states()
