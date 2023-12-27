from helpers.dbaccess import MongoDbAccess
import logging
import subprocess
from helpers.interfaces import DeviceManagerInterface, NetwatcherInterface

class HomeKeeperNetwatcher(NetwatcherInterface):

    def __init__(self, device_manager: DeviceManagerInterface, logger: logging.Logger) -> None:
        self.__device_states = {}
        self.__device_manager = device_manager
        self.__logger = logger

    def __process_device_state(self, res: bool, ip_addr: str, name: str):
        if ip_addr not in self.__device_states:
            self.__device_states[ip_addr] = {
                "state": res,
                "counter": 0
            }

        if self.__device_states[ip_addr]["state"] != res:
            counter_threshold = 5 if not res else 1
            if self.__device_states[ip_addr]["counter"] >= counter_threshold:
                self.__device_manager.mobile_device_connect_disconnect_handler(name, res)
                self.__device_states[ip_addr]["state"] = res
                self.__device_states[ip_addr]["counter"] = 0
                self.__logger.info("device state counter reset")
            else:
                self.__logger.info("device state counter incremented")
                self.__device_states[ip_addr]["counter"] += 1

    def ping_mobile_devices(self):
        with MongoDbAccess() as mongo_client:
            for mobile_device in mongo_client.get_mobile_devices():
                device_name = mobile_device['mobile_device_name']
                ip_addr = mobile_device['ip_address']
                self.__logger.info(f'processing {device_name}')
                try:
                    subprocess.check_output(['ping', '-c', '1', ip_addr])
                    logging.info(f'{device_name} ping successfully')
                    response = True
                except:
                    logging.info(f'{device_name} ping failed')
                    response = False
                self.__process_device_state(response, ip_addr, device_name)