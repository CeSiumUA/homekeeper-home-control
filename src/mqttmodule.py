import logging
from paho.mqtt import client as mqtt_client
import topics
import random
from dailyevents import DailyEvent
from env import Env

def __on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT")
    else:
        logging.fatal("Failed to connect to MQTT, return code: %d\n", rc)

def __on_message(client: mqtt_client.Client, userdata, msg):
    logging.info(f'userdata: {userdata}')
    logging.info(f'message: {msg.payload.decode()}')

def start_mqtt_client(broker_host: str, broker_port: int, broker_username : str | None = None, broker_password: str | None = None):
    global MQTT_CLIENT_INSTANCE

    client_id = "horizon-hues-{}".format(random.randint(0, 1000))

    MQTT_CLIENT_INSTANCE = mqtt_client.Client(client_id=client_id)
    MQTT_CLIENT_INSTANCE.on_connect = __on_mqtt_connect
    MQTT_CLIENT_INSTANCE.on_message = __on_message
    if broker_username is not None:
        MQTT_CLIENT_INSTANCE.username_pw_set(broker_username, broker_password)
    MQTT_CLIENT_INSTANCE.connect(broker_host, broker_port)
    MQTT_CLIENT_INSTANCE.loop_start()

def subscribe_to_device(device_name: str, qos: int = 2):
    topic_name = topics.get_tasmota_stat_result_topic(device=device_name)
    MQTT_CLIENT_INSTANCE.subscribe(topic=topic_name, qos=qos)
    MQTT_CLIENT_INSTANCE.message_callback_add(topic_name, __on_message)