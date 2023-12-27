from helpers.dbaccess import MongoDbAccess
import logging
from helpers.dailyevents import DailyEvent
import datetime
from helpers.devicestatemachinevalidator import DeviceStateBasicValidator, DeviceSwitchTimeValidator
from helpers.interfaces import DeviceManagerInterface, MqttPublisherInterface

class DevicesManager(DeviceManagerInterface):

    def __init__(self, publisher: MqttPublisherInterface, logger: logging.Logger) -> None:
        super().__init__()
        self.__publisher = publisher
        self.__logger = logger

    def __toggle_device(self, mongo_client: MongoDbAccess, device, state: bool | None = None, forced: bool = False, is_user_forced: bool = False):
        
        if is_user_forced or forced:
            validator = DeviceSwitchTimeValidator(device, self.__logger)
            if not is_user_forced:
                forced = False
        else:
            validator = DeviceStateBasicValidator.get_device_validator(device, self.__logger)

        if validator.is_toggle_allowed(new_state=state, forced=forced):
            
            current_time = datetime.datetime.now()

            mongo_client.update_device_stats(device_name=validator.device_name, last_switch=current_time, forced_power=validator.is_power_forced)

            self.__logger.info(f"last switch time updated for {validator.device_name}")

            self.__publisher.send_device_toggle(device_name=validator.device_name)

            self.__logger.info(f"MQTT signal sent to {validator.device_name}")

    def process_device_states(self, get_active_devices: bool = True):
        with MongoDbAccess() as mongo_client:
            if get_active_devices:
                for device_group in mongo_client.get_devices_with_mobile_pair():
                    device = device_group['device']
                    self.__toggle_device(mongo_client=mongo_client, device=device)
            else:
                offline_mobile_devices = list(mongo_client.get_offline_mobile_devices())
                projected_offline_devices = [md[MongoDbAccess.MOBILE_DEVICE_NAME_FIELD] for md in offline_mobile_devices]
                self.__logger.info(f"got offline devices: {projected_offline_devices}")
                for device in mongo_client.get_paired_devices(projected_offline_devices):
                    self.__logger.info(f"processing device: {device}")
                    device_mobile_devices = device[MongoDbAccess.DEVICE_PAIRED_DEVICES_FIELD]
                    are_all_mobile_devices_offline = all(md in projected_offline_devices for md in device_mobile_devices)
                    if are_all_mobile_devices_offline:
                        self.__toggle_device(mongo_client=mongo_client, device=device, state=False, forced=True, is_user_forced=False)
                    else:
                        self.__logger.info("device has still some mobiles connected to network")

    def mobile_device_connect_disconnect_handler(self, mobile_device_name: str, is_connected: bool):
        self.__logger.info(f"updating mobile device ({mobile_device_name}) state (connected: {is_connected})")
        with MongoDbAccess() as mongo_client:
            mongo_client.update_mobile_device_stat(mobile_device_name, is_connected)
        self.__logger.info("mobile devices states updated")
        self.process_device_states(is_connected)

    def device_direct_command_handler(self, device_name: str, state: bool):
        with MongoDbAccess() as mongo_client:
            device = mongo_client.get_device_by_name(device_name=device_name)
            if device is None:
                self.__logger.info(f"device {device_name} not found")
                return
            self.__toggle_device(mongo_client=mongo_client, state=state, device=device, forced=True, is_user_forced=True)

    def time_event_handler(self, event_type: DailyEvent, devices):
        self.__logger.info(f"updating devices state: {event_type}")

        with MongoDbAccess() as mongo_client:
            if event_type == DailyEvent.BED_TIME or event_type == DailyEvent.WAKEUP_TIME:
                mongo_client.update_devices_sleep(event_type == DailyEvent.BED_TIME)
            elif event_type == DailyEvent.SUNRISE or event_type == DailyEvent.SUNSET:
                mongo_client.update_devices_dark(event_type == DailyEvent.SUNSET)
            else:
                # TODO implement other events
                self.__logger.info(f"unknown event type: {event_type}")
                return
        self.__logger.info(f"devices state update finished")
        self.process_device_states()
