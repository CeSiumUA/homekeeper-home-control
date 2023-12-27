import logging
from paho.mqtt import client as mqtt_client
import helpers.topics
import random
from helpers.dailyevents import DailyEvent
from helpers.env import Env
from helpers.dbaccess import MongoDbAccess
import json
from helpers.interfaces import DeviceManagerInterface, MqttPublisherInterface, TelegramMessageSenderInterface

class HomeKeeperMQTT(mqtt_client.Client, MqttPublisherInterface):

    TASMOTA_DEVICE_POWER_STATUS = "POWER"
    TASMOTA_DEVICE_ANALOG_STATUS = "ANALOG"
    TASMOTA_DEVICE_ANALOG_TEMPERATURE_STATUS = "Temperature"
    TASMOTA_DEVICE_ENERGY_STATUS = "ENERGY"
    TASMOTA_DEVICE_ENERGY_TOTAL_STATUS = "Total"

    TASMOTA_DEVICE_TOGGLE_COMMAND = 'toggle'
    TASMOTA_DEVICE_ON_COMMAND = 'on'
    TASMOTA_DEVICE_OFF_COMMAND = 'off'
    
    def __init__(self, tl_message_sender: TelegramMessageSenderInterface, device_manager: DeviceManagerInterface, logger: logging.Logger) -> None:
        client_id = "home-control-{}".format(random.randint(0, 1000))
        super().__init__(client_id)
        self.__tl_message_sender = tl_message_sender
        self.__device_manager = device_manager
        self.__logger = logger

    def __on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.__logger.info("Connected to MQTT")
        else:
            self.__logger.fatal("Failed to connect to MQTT, return code: %d\n", rc)

    def __enter__(self):
        self.start_mqtt_client()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.loop_stop()

    @mqtt_client.Client.on_connect.getter
    def on_connect(self):
        return self.__on_mqtt_connect

    def start_mqtt_client(self):
        broker_host, broker_port, broker_username, broker_password = Env.get_mqtt_connection_params()

        if broker_username is not None:
            self.username_pw_set(broker_username, broker_password)
        self.connect(broker_host, broker_port)

        self.loop_start()

    def subscribe_to_device(self, device_name: str, qos: int = 2):
        power_topic_name = helpers.topics.get_tasmota_stat_result_topic(device=device_name)
        sensor_topic_name = helpers.topics.get_tasmota_sensor_topic(device=device_name)

        self.subscribe(topic=power_topic_name, qos=qos)
        self.message_callback_add(power_topic_name, self.on_device_result_message)

        self.subscribe(topic=sensor_topic_name, qos=qos)
        self.message_callback_add(sensor_topic_name, self.on_device_sensor_message)

    def subscribe_to_devices(self, devices = None):
        with MongoDbAccess() as mongo_client:
            if devices is None:
                devices = mongo_client.get_devices_names()
            for device_set in devices:
                device_name = device_set[MongoDbAccess.DEVICE_NAME_FIELD]
                self.subscribe_to_device(device_name=device_name)
                self.__logger.info(f"subscribed to device: {device_name}")

    def subscribe_to_telegram_message_sending(self):
        self.subscribe(topic=helpers.topics.SEND_MESSAGE, qos=2)
        self.message_callback_add(helpers.topics.SEND_MESSAGE, self.on_telegram_message_request)

    def subscribe_to_topics(self):
        self.subscribe_to_devices()
        self.subscribe_to_telegram_message_sending()


    def get_device_stat(self, device_name: str, qos: int = 2):
        topic_name = helpers.topics.get_tasmota_power_cmnd_topic(device=device_name)
        self.publish(topic=topic_name, qos=qos)

    def get_devices_stat(self):
        self.__logger.info('getting devices stat...')
        with MongoDbAccess() as mongo_client:
            for device_set in mongo_client.get_devices_names():
                device_name = device_set[MongoDbAccess.DEVICE_NAME_FIELD]
                self.__logger.info(f'getting stat from: {device_name}')
                self.get_device_stat(device_name=device_name)

    def send_device_toggle(self, device_name: str, qos: int = 2, state: bool | None = None):
        if state is None:
            command = HomeKeeperMQTT.TASMOTA_DEVICE_TOGGLE_COMMAND
        else:
            command = HomeKeeperMQTT.TASMOTA_DEVICE_ON_COMMAND if state else HomeKeeperMQTT.TASMOTA_DEVICE_OFF_COMMAND
        # temporary
        if Env.get_publish_to_tg():
            self.__logger.info("publishing to tg...")
            self.publish(topic=helpers.topics.SEND_MESSAGE, payload=f"device {device_name} should be {command} now!")

        if Env.get_publish_to_tasmota():
            publish_topic = helpers.topics.get_tasmota_power_cmnd_topic(device=device_name)
            self.__logger.info(f"publishing to tasmota device on topic {publish_topic}, command: {command}")
            self.publish(publish_topic, command)

    def on_telegram_message_request(self, client: mqtt_client.Client, userdata, msg):
        self.__tl_message_sender.send_telegram_message(msg.payload.decode())

    def on_device_sensor_message(self, client: mqtt_client.Client, userdata, msg):
        segments = msg.topic.split('/')
        if len(segments) != 3:
            self.__logger.error("topic segments are not equal to 3...")
        device_name = segments[1]

        payload = msg.payload.decode()
        self.__logger.info(f"got MQTT message on topic: {msg.topic}, payload: {payload}")
        sensor_json = json.loads(payload)

        energy = sensor_json[HomeKeeperMQTT.TASMOTA_DEVICE_ENERGY_STATUS][HomeKeeperMQTT.TASMOTA_DEVICE_ENERGY_TOTAL_STATUS]

        device_sensor_stats = {
            MongoDbAccess.DEVICE_TOTAL_ENERGY_FIELD: energy
        }

        if HomeKeeperMQTT.TASMOTA_DEVICE_ANALOG_STATUS in sensor_json:
            analog_section = sensor_json[HomeKeeperMQTT.TASMOTA_DEVICE_ANALOG_STATUS]
            if HomeKeeperMQTT.TASMOTA_DEVICE_ANALOG_TEMPERATURE_STATUS in analog_section:
                temperature = analog_section[HomeKeeperMQTT.TASMOTA_DEVICE_ANALOG_TEMPERATURE_STATUS]
                device_sensor_stats[MongoDbAccess.DEVICE_TEMPERATURE_FIELD] = temperature

        self.__logger.info(f'got payload on topic: {msg.topic} from sensor: {payload}')

        with MongoDbAccess() as mongo_client:
            mongo_client.update_device_sensor_stats(device_name, device_sensor_stats)

        self.__device_manager.process_device_states()

    def on_device_result_message(self, client: mqtt_client.Client, userdata, msg):
        segments = msg.topic.split('/')
        if len(segments) != 3:
            self.__logger.error("topic segments are not equal to 3...")
        device_name = segments[1]

        payload = msg.payload.decode()
        self.__logger.info(f"got MQTT message on topic: {msg.topic}, payload: {payload}")
        stat_json = json.loads(payload)
        is_power_on = True if stat_json[HomeKeeperMQTT.TASMOTA_DEVICE_POWER_STATUS] == HomeKeeperMQTT.TASMOTA_DEVICE_ON_COMMAND.upper() else False

        self.__logger.info(f"got device state on topic: {msg.topic}, is power on: {is_power_on}, device name: {device_name}")

        with MongoDbAccess() as mongo_client:
            mongo_client.update_device_power_on(device_name=device_name, power_on=is_power_on)