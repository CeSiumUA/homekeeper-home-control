import suntime
import datetime
import logging
from helpers.env import Env
from helpers.dailyevents import DailyEvent
from apscheduler.schedulers.background import BackgroundScheduler
from helpers.dbaccess import MongoDbAccess
from helpers.interfaces import NetwatcherInterface, DeviceManagerInterface, MqttPublisherInterface

class HomeKeeperScheduler(BackgroundScheduler):

    def __init__(self, netwatcher: NetwatcherInterface, device_manager: DeviceManagerInterface, mqtt_publisher: MqttPublisherInterface, logger: logging.Logger):
        super().__init__()
        self.__netwatcher = netwatcher
        self.__device_manager = device_manager
        self.__mqtt_publisher = mqtt_publisher
        self.__logger = logger

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown(wait=False)

    def __calculate_dusk_dawn(self):
        sun_obj = suntime.Sun(lat=self.__latitude, lon=self.__longitude)
        today = datetime.date.today()

        today_sunrise = sun_obj.get_local_sunrise_time(today)
        today_sunset = sun_obj.get_local_sunset_time(today)

        return today_sunrise, today_sunset

    def __get_tomorrow_zero_hour(self, curr_datetime: datetime.datetime | None = None):
        if curr_datetime is None:
            curr_datetime = datetime.datetime.now()
        tomorrow = curr_datetime + datetime.timedelta(days=1)
        tomorrow_zero_hour = tomorrow.replace(hour=0, minute=1)
        return tomorrow_zero_hour
    
    def __timing_event_fn(self, event_type: DailyEvent, devices = None):
        self.__device_manager.time_event_handler(event_type, devices)
        
    def __sunrise_event(self):
        self.__timing_event_fn(DailyEvent.SUNRISE)

    def __sunset_event(self):
        self.__timing_event_fn(DailyEvent.SUNSET)
    
    def __zero_hour_event(self):
        sr, ss = self.__calculate_dusk_dawn()
        
        tomorrow_zero_hour = self.__get_tomorrow_zero_hour()

        sunrise_event = self.__sunrise_event
        sunset_event = self.__sunset_event

        self.add_planned_job(sunrise_event, run_date=sr)
        self.add_planned_job(sunset_event, run_date=ss)
        self.add_planned_job(self.__zero_hour_event, run_date=tomorrow_zero_hour)

    def add_cron_job(self, job, hour: int, minute: int, args = None):
        self.add_job(job, 'cron', hour=hour, minute=minute, args=args)

    def add_planned_job(self, job, run_date: datetime.datetime):
        self.add_job(job, 'date', run_date=run_date)

    def register_timing_events(self):

        longitude, latitude = Env.get_device_lon_lat()

        self.__longitude = float(longitude)
        self.__latitude = float(latitude)
        sr, ss = self.__calculate_dusk_dawn()
        
        current_datetime = datetime.datetime.now()

        if current_datetime.timestamp() < sr.timestamp():
            next_run = sr
            scheduled_fn = self.__sunrise_event
            self.add_planned_job(scheduled_fn, next_run)
        elif current_datetime.timestamp() > sr.timestamp() and current_datetime.timestamp() < ss.timestamp():
            next_run = ss
            scheduled_fn = self.__sunset_event
            self.add_planned_job(scheduled_fn, next_run)

        zero_hour_job_date = self.__get_tomorrow_zero_hour()
        if zero_hour_job_date is None:
            self.__logger.fatal("can't set zero hour event for tomorrow")

        self.add_planned_job(self.__zero_hour_event, zero_hour_job_date)

    def register_device_ping_events(self, timebase: datetime.datetime | None = None):
        if timebase is None:
            timebase = datetime.datetime.now()
        stats_run_time = timebase + datetime.timedelta(minutes=1)
        self.add_job(self.__mqtt_publisher.get_devices_stat, 'interval', minutes=20, start_date=stats_run_time)

    def register_stored_jobs(self):
        with MongoDbAccess() as mongo_db_access:
            cursor = mongo_db_access.get_timings()
            if cursor is None:
                self.__logger.fatal("error to get mongo collection")

            for schedule in cursor:
                schedule_type = schedule["type"]
                if schedule_type not in DailyEvent._value2member_map_:
                    self.__logger.error(f'invalid event type: {schedule_type}')
                    continue
                daily_event = DailyEvent(schedule_type)
                # affected_devices = schedule["devices"]

                self.add_cron_job(self.__timing_event_fn, schedule["hour"], schedule["minute"], args=(daily_event, None))

    def register_mobile_ping_job(self):
        interval = Env.get_mobile_device_ping_interval()

        self.add_job(self.__netwatcher.ping_mobile_devices, 'interval', seconds=interval)

    def register_all_jobs(self):
        self.register_timing_events()
        self.register_device_ping_events()
        self.register_stored_jobs()
        self.register_mobile_ping_job()