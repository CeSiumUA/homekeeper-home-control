from enum import Enum


class DailyEvent(Enum):
    SUNRISE = "sunrise_time"
    SUNSET = "sunset_time"
    WAKEUP_TIME = "wakeup_time"
    BED_TIME = "bed_time"
    CUSTOM_TIME_ON = "custom_time_on"
    CUSTOM_TIME_OFF = "custom_time_off"
    CUSTOM_TIME_TOGGLE = "custom_time_toggle"