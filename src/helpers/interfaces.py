from helpers.dailyevents import DailyEvent


class DeviceManagerInterface:
    def device_direct_command_handler(self, device_name: str, state: bool):
        raise NotImplementedError
    
    def time_event_handler(self, event_type: DailyEvent, devices):
        raise NotImplementedError
    
    def mobile_device_connect_disconnect_handler(self, mobile_device_name: str, is_connected: bool):
        raise NotImplementedError
    
    def process_device_states(self, get_active_devices: bool = True):
        raise NotImplementedError
    
class MqttPublisherInterface:
    def publish(self, topic: str, payload: str | None = None, qos: int = 2):
        raise NotImplementedError
    
    def get_devices_stat(self):
        raise NotImplementedError
    
    def send_device_toggle(self, device_name: str, qos: int = 2, state: bool | None = None):
        raise NotImplementedError
    
class NetwatcherInterface:
    def ping_mobile_devices(self):
        raise NotImplementedError
    
class TelegramMessageSenderInterface:
    def send_telegram_message(self, message: str):
        raise NotImplementedError
    
class DependencyContainer(DeviceManagerInterface, MqttPublisherInterface, NetwatcherInterface, TelegramMessageSenderInterface):
    def register_dependencies(self, device_manager: DeviceManagerInterface, publisher: MqttPublisherInterface, netwatcher: NetwatcherInterface, tl_sender: TelegramMessageSenderInterface):
        self.__device_manager = device_manager
        self.__publisher = publisher
        self.__netwatcher = netwatcher
        self.__tl_sender = tl_sender

    def device_direct_command_handler(self, device_name: str, state: bool):
        return self.__device_manager.device_direct_command_handler(device_name=device_name, state=state)
    
    def time_event_handler(self, event_type: DailyEvent, devices):
        return self.__device_manager.time_event_handler(event_type=event_type, devices=devices)
    
    def mobile_device_connect_disconnect_handler(self, mobile_device_name: str, is_connected: bool):
        return self.__device_manager.mobile_device_connect_disconnect_handler(mobile_device_name=mobile_device_name, is_connected=is_connected)
    
    def process_device_states(self, get_active_devices: bool = True):
        return self.__device_manager.process_device_states(get_active_devices=get_active_devices)

    def publish(self, topic: str, payload: str | None = None, qos: int = 2):
        return self.__publisher.publish(topic=topic, payload=payload, qos=qos)
    
    def get_devices_stat(self):
        return self.__publisher.get_devices_stat()
    
    def send_device_toggle(self, device_name: str, qos: int = 2, state: bool | None = None):
        return self.__publisher.send_device_toggle(device_name=device_name, qos=qos, state=state)
    
    def ping_mobile_devices(self):
        return self.__netwatcher.ping_mobile_devices()
    
    def send_telegram_message(self, message: str):
        return self.__tl_sender.send_telegram_message(message=message)