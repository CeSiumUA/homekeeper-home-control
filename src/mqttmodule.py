import logging
from paho.mqtt import client as mqtt_client
import topics
import random
from dailyevents import DailyEvent
from env import Env
from dbaccess import MongoDbAccess
import json
import devices

TASMOTA_DEVICE_TOGGLE_COMMAND = 'toggle'
TASMOTA_DEVICE_ON_COMMAND = 'on'
TASMOTA_DEVICE_OFF_COMMAND = 'off'

def __on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT")
    else:
        logging.fatal("Failed to connect to MQTT, return code: %d\n", rc)

def __device_connect_disconnect(client: mqtt_client.Client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    mobile_device_name = payload['mobile_device']
    state = bool(payload['state'])

    logging.info(f"device {mobile_device_name}, state: {state}")

    devices.device_connect_disconnect_handler(mobile_device_name=mobile_device_name, is_connected=state)

def __timing_event(client: mqtt_client.Client, userdata, msg):
    event = DailyEvent(msg.payload.decode())

    logging.info(f"timing event: {event.name}")

    devices.time_event_handler(event)

def __device_toggle_command(client: mqtt_client.Client, userdata, msg):
    payload = json.loads(msg.payload.decode())

    device_name = payload['device_name']
    state = payload['state']

    logging.info(f"command to set device {device_name} to powered: {state}")

    devices.device_direct_command_handler(device_name=device_name, state=state)

def __on_device_result_message(client: mqtt_client.Client, userdata, msg):
    segments = msg.topic.split('/')
    if len(segments) != 3:
        logging.error("topic segments are not equal to 3...")
    device_name = segments[1]

    payload = msg.payload.decode()
    stat_json = json.loads(payload)
    is_power_on = True if stat_json["POWER"] == "ON" else False

    logging.info(f"got device state on topic: {msg.topic}, is power on: {is_power_on}, device name: {device_name}")

    with MongoDbAccess() as mongo_client:
        mongo_client.update_device_power_on(device_name=device_name, power_on=is_power_on)

def start_mqtt_client(broker_host: str, broker_port: int, broker_username : str | None = None, broker_password: str | None = None):
    global MQTT_CLIENT_INSTANCE

    client_id = "horizon-hues-{}".format(random.randint(0, 1000))

    MQTT_CLIENT_INSTANCE = mqtt_client.Client(client_id=client_id)
    MQTT_CLIENT_INSTANCE.on_connect = __on_mqtt_connect
    if broker_username is not None:
        MQTT_CLIENT_INSTANCE.username_pw_set(broker_username, broker_password)
    MQTT_CLIENT_INSTANCE.connect(broker_host, broker_port)

    MQTT_CLIENT_INSTANCE.subscribe(topic=topics.DEVICE_CONNECT_DISCONNECT, qos=2)
    MQTT_CLIENT_INSTANCE.message_callback_add(topics.DEVICE_CONNECT_DISCONNECT, __device_connect_disconnect)

    MQTT_CLIENT_INSTANCE.subscribe(topic=topics.TIMING_EVENT, qos=2)
    MQTT_CLIENT_INSTANCE.message_callback_add(topics.TIMING_EVENT, __timing_event)

    MQTT_CLIENT_INSTANCE.subscribe(topic=topics.DEVICE_TOGGLE, qos=2)
    MQTT_CLIENT_INSTANCE.message_callback_add(topics.DEVICE_TOGGLE, __device_toggle_command)

    MQTT_CLIENT_INSTANCE.loop_start()

def subscribe_to_device(device_name: str, qos: int = 2):
    topic_name = topics.get_tasmota_stat_result_topic(device=device_name)
    MQTT_CLIENT_INSTANCE.subscribe(topic=topic_name, qos=qos)
    MQTT_CLIENT_INSTANCE.message_callback_add(topic_name, __on_device_result_message)

def get_device_stat(device_name: str, qos: int = 2):
    topic_name = topics.get_tasmota_power_cmnd_topic(device=device_name)
    MQTT_CLIENT_INSTANCE.publish(topic=topic_name, qos=qos)

def send_device_toggle(device_name: str, qos: int = 2, state: bool | None = None):
    if state is None:
        command = TASMOTA_DEVICE_TOGGLE_COMMAND
    else:
        command = TASMOTA_DEVICE_ON_COMMAND if state else TASMOTA_DEVICE_OFF_COMMAND
    # temporary
    if Env.get_publish_to_tg():
        logging.info("publishing to tg...")
        MQTT_CLIENT_INSTANCE.publish(topic=topics.SEND_MESSAGE, payload=f"device {device_name} should be {command} now!")

    if Env.get_publish_to_tasmota():
        publish_topic = topics.get_tasmota_power_cmnd_topic(device=device_name)
        logging.info(f"publishing to tasmota device on topic {publish_topic}, command: {command}")
        MQTT_CLIENT_INSTANCE.publish(publish_topic, command)