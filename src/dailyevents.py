from enum import Enum


class DailyEvent(Enum):
    SUNRISE = "sunrise_time"
    SUNSET = "sunset_time"
    WAKEUP_TIME = "wakeup_time"
    BED_TIME = "bed_time"
    CUSTOM_TIME = "custom_time"