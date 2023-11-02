VIDEO_DOWNLOAD = 'video_downloader'
GET_IP_ADDRESS = 'ip-address'
SEND_MESSAGE = 'send_message'
TIMING_EVENT = 'timing_event'
DEVICE_CONNECT_DISCONNECT = 'device_connect_disconnect'
DEVICE_TOGGLE = 'device_toggle'
TASMOTA_POWER_CMND_TEMPLATE = 'cmnd/~/Power'
TASMOTA_POWER_STAT_TEMPLATE = 'stat/~/POWER'
TASMOTA_STAT_RESULT_TEMPLATE = 'stat/~/RESULT'

def get_tasmota_power_cmnd_topic(device: str):
    return TASMOTA_POWER_CMND_TEMPLATE.replace("~", device)

def get_tasmota_power_stat_topic(device: str):
    return TASMOTA_POWER_STAT_TEMPLATE.replace("~", device)

def get_tasmota_stat_result_topic(device: str):
    return TASMOTA_STAT_RESULT_TEMPLATE.replace("~", device)