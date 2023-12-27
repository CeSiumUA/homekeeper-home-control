from os import environ
import logging

class Env:
    MQTT_HOST = "MQTT_HOST"
    MQTT_PORT = "MQTT_PORT"
    MQTT_USERNAME = "MQTT_USERNAME"
    MQTT_PASSWORD = "MQTT_PASSWORD"
    MONGO_URL = "MONGO_URL"
    MONGO_HOMEKEEPER_DB = "MONGO_HOMEKEEPER_DB"
    MONGO_HOMEKEEPER_LOGS_DB = "MONGO_HOMEKEEPER_LOGS_DB"
    MONGO_HOMEKEEPER_CONTROL_LOGS_COLL = "MONGO_HOMEKEEPER_CONTROL_LOGS_COLL"
    MONGO_DEVICES_COLL = "MONGO_DEVICES_COLL"
    MONGO_MOBILE_DEVICES_COLL = "MONGO_MOBILE_DEVICES_COLL"
    MONGO_SCHEDULES_COLL = "MONGO_SCHEDULES_COLL"
    PUBLISH_TO_TG = "PUBLISH_TO_TG"
    PUBLISH_TO_TASMOTA = "PUBLISH_TO_TASMOTA"
    DEVICE_LON = "DEVICE_LONGITUDE"
    DEVICE_LAT = "DEVICE_LATITUDE"
    PING_INTERVAL = "PING_INTERVAL"
    TL_CHAT_ID = "CHAT_ID"
    TL_TOKEN = "TL_TOKEN"

    def get_mqtt_connection_params():
        broker_host = environ.get(Env.MQTT_HOST)
        broker_port = environ.get(Env.MQTT_PORT)
        if broker_port is None:
            broker_port = 1883
        else:
            broker_port = int(broker_port)

        broker_username = environ.get(Env.MQTT_USERNAME)
        broker_password = environ.get(Env.MQTT_PASSWORD)

        return broker_host, broker_port, broker_username, broker_password
        
    def get_mongo_connection_url():
        mongo_url = environ.get(Env.MONGO_URL)
        return mongo_url
    
    def get_mongo_db_name():
        return environ.get(Env.MONGO_HOMEKEEPER_DB)
    
    def get_mongo_logs_db_name():
        return environ.get(Env.MONGO_HOMEKEEPER_LOGS_DB)
    
    def get_mongo_logs_coll_name():
        return environ.get(Env.MONGO_HOMEKEEPER_CONTROL_LOGS_COLL)
    
    def get_mongo_devices_coll_name():
        return environ.get(Env.MONGO_DEVICES_COLL)
    
    def get_mongo_mobile_devices_coll_name():
        return environ.get(Env.MONGO_MOBILE_DEVICES_COLL)
    
    def get_mongo_schedules_coll_name():
        return environ.get(Env.MONGO_SCHEDULES_COLL)
    
    def get_device_lon_lat():
        lon = environ.get(Env.DEVICE_LON)
        lat = environ.get(Env.DEVICE_LAT)

        return lon, lat

    def get_mobile_device_ping_interval():
        ping_interval = environ.get(Env.PING_INTERVAL)

        if ping_interval is None:
            ping_interval = 30
        else:
            ping_interval = int(ping_interval)

        return ping_interval

    def get_publish_to_tg():
        publish_to_tg = environ.get(Env.PUBLISH_TO_TG)

        if publish_to_tg is None:
            return False
        
        return int(publish_to_tg) == 1
    
    def get_publish_to_tasmota():
        publish_to_tasmota = environ.get(Env.PUBLISH_TO_TASMOTA)

        if publish_to_tasmota is None:
            return False
        
        return int(publish_to_tasmota) == 1
    
    def get_tl_token():
        return environ.get(Env.TL_TOKEN)
    
    def get_tl_chat_id():
        return int(environ.get(Env.TL_CHAT_ID))
    
    def load_required_values():
        """
        Returns
        -------
        bool
            True, if all required values are present, 
        or False if some variables are missing.
        Description
        -----------
        Loads all required environment variables, and returns True if all values are present
        """
        broker_host, broker_port, broker_username, broker_password = Env.get_mqtt_connection_params()
        if broker_host is None:
            logging.error("broker host is empty")
            return False

        mongo_connection_uri = Env.get_mongo_connection_url()
        if mongo_connection_uri is None:
            logging.error("mongo uri is empty")
            return False
        
        homekeeper_db_name = Env.get_mongo_db_name()
        if homekeeper_db_name is None:
            logging.error("homekeeper db is empty")
            return False

        homekeeper_devices_coll_name = Env.get_mongo_devices_coll_name()
        if homekeeper_devices_coll_name is None:
            logging.error("homekeeper devices collection is empty")
            return False
        
        homekeeper_mobile_devices_coll_name = Env.get_mongo_mobile_devices_coll_name()
        if homekeeper_mobile_devices_coll_name is None:
            logging.error("homekeeper mobile devices collection is empty")
            return False
        
        homekeeper_schedules_coll_name = Env.get_mongo_schedules_coll_name()
        if homekeeper_schedules_coll_name is None:
            logging.error('homekeeper schedules collection is empty')
            return False

        lon, lat = Env.get_device_lon_lat()
        if lon is None or lat is None:
            logging.error(f"homekeeper longitude or latitude not set, values: {lon}, {lat}")
            return False
        
        tl_token = Env.get_tl_token()
        if tl_token is None:
            logging.error('telegram token is empty')
            return False
        
        tl_chat_id = Env.get_tl_chat_id()
        if tl_chat_id is None:
            logging.error('telegram chat id is empty')
            return False

        return True